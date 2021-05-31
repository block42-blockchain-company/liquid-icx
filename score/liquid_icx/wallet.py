from .scorelib.utils import *
from iconservice import *


class Wallet:
    __sys_score = IconScoreBase.create_interface_score(SYSTEM_SCORE, InterfaceSystemScore)

    def __init__(self, db: IconScoreDatabase, _address: Address):
        self._address = _address
        self._locked = VarDB("locked_" + str(_address), db, value_type=int)
        self._unstaking = VarDB("unstaking_" + str(_address), db, value_type=int)

        # Presents how much user deposited to SCORE in chronological order
        self._join_values = ArrayDB("join_values_" + str(_address), db, value_type=int)
        self._unlock_heights = ArrayDB("unlock_heights" + str(_address), db, value_type=int)

        # Presents with how much LICX user wants to leave in chronological order
        self._leave_values = ArrayDB("leave_values_" + str(_address), db, value_type=int)
        self._unstake_heights = ArrayDB("unstake_heights_" + str(_address), db, value_type=int)

        # Wallet ID in linked list
        self._node_id = VarDB("node_id_" + str(_address), db, value_type=int)

        # Tracking individual wallet's delegations
        self._delegation_address = ArrayDB("delegation_address_" + str(_address), db, value_type=Address)
        self._delegation_value = ArrayDB("delegation_value_" + str(_address), db, value_type=int)

    def join(self, _join_amount: int, _delegation: dict, _licx: IconScoreBase):
        """
        Adds new values to the wallet's join queue
        It also tracks the delegations of each wallet
        :param _join_amount: amount of ICX that a wallet sent
        :param _delegation: delegations as dictionary
        :param _licx: licx instance, to modify '_delegation' and '_delegation_keys' db variables
        """

        if len(self._join_values) >= 10:
            revert("LiquidICX: Wallet tries to join more than 10 times in 2 terms. This is considered as spam")

        iiss_info = self.__sys_score.getIISSInfo()

        self._join_values.put(_join_amount)
        self._unlock_heights.put(iiss_info["nextPRepTerm"] + TERM_LENGTH)
        self.locked = self.locked + _join_amount

        delegation_amount_sum = 0
        for address, value in _delegation.items():
            self.add_single_delegation(_licx, address, value)
            delegation_amount_sum += value

        if delegation_amount_sum != _join_amount:
            revert("LiquidICX: Delegations values do not match to the amount of ICX sent.")

    def request_leave(self, _leave_amount: int):
        """
        Adds a leave amount to the wallet's leave queue.
        :param _leave_amount: Amount of LICX for a leave request
        """

        if len(self._leave_values) >= 10:
            revert("LiquidICX: Wallet has already 10 leave requests. This is considered a spam")

        self._leave_values.put(_leave_amount)
        self.unstaking = self.unstaking + _leave_amount

    def leave(self, _licx: IconScoreBase) -> int:
        """
        Function resolves a leave request.
        It sum up the value and adds an unstaking period of all un-resolved leave requests.

        The sum of leaving values is proportionally subtracted from all delegated addresses.
        Let's assume, that sender is delegating 123 ICX(35,76%) to prep_1 and 221 ICX(64,24%) to prep_2.
        User leaving with 150 ICX means, that 53,64 ICX will be subtracted from prep_1 and 96,36 ICX from prep_2.

        :return: Sum of newly resolved leave requests
        """

        leave_amount = 0
        if len(self._leave_values) != len(self._unstake_heights):
            current_height = self.__sys_score.getIISSInfo()["blockHeight"]
            unstake_period = self.__sys_score.estimateUnstakeLockPeriod()["unstakeLockPeriod"]
            # add unstaking period
            for it in range(len(self._unstake_heights), len(self._leave_values)):
                leave_amount += self._leave_values[it]
                self._unstake_heights.put(current_height + unstake_period + UNSTAKING_MARGIN)

            self.subtract_delegations_proportionally_to_wallet(_licx, leave_amount)

        return leave_amount

    def unlock(self) -> int:
        """
        Unlocks user's LICX and removes entry from the _join_values, _allow_transfer_height
        :return: Amount of new unlocked LICX
        """

        unlocked = 0
        if self.locked > 0:
            next_term = self.__sys_score.getIISSInfo()["nextPRepTerm"]
            while self._unlock_heights:
                if next_term > self._unlock_heights[0]:  # always check and remove the first element only
                    self.locked = self.locked - self._join_values[0]

                    unlocked += self._join_values[0]

                    Utils.remove_from_array(self._join_values, self._join_values[0])
                    Utils.remove_from_array(self._unlock_heights, self._unlock_heights[0])
                else:
                    break
        return unlocked

    def claim(self) -> int:
        """
        Function checks, if the user's unstaking period is over and his is ICX is ready to be claimed.
        """

        claim_amount = 0
        if len(self._unstake_heights):
            block_height = self.__sys_score.getIISSInfo()["blockHeight"]
            while len(self._unstake_heights):
                if block_height >= self._unstake_heights[0]:
                    claim_amount = claim_amount + self._leave_values[0]
                    self.unstaking = self.unstaking - self._leave_values[0]

                    Utils.remove_from_array(self._leave_values, self._leave_values[0])
                    Utils.remove_from_array(self._unstake_heights, self._unstake_heights[0])
                else:
                    break
        return claim_amount

    def add_single_delegation(self, _licx: IconScoreBase, _address: str, _value: int):
        prep_address: Address = Address.from_string(_address)

        # If prep_address is already in the wallet's delegation
        if prep_address in self._delegation_address:
            index = list(self._delegation_address).index(prep_address)
            self._delegation_value[index] += _value
            _licx._delegation[prep_address] += _value
        else:
            # If prep_address already exists in global licx delegations
            if prep_address in _licx._delegation_keys:
                _licx._delegation[prep_address] += _value
            # Make sure prep_address is actually a prep
            elif not Utils.isPrep(_licx.db, prep_address):
                revert("LiquidICX: Given address is not a P-Rep.")
            else:
                _licx._delegation_keys.put(prep_address)
                _licx._delegation[prep_address] = _value
            # Always add to the wallet's array because prep_address is not yet part of the wallet's delegation
            self._delegation_address.put(prep_address)
            self._delegation_value.put(_value)

    def subtract_delegations_proportionally_to_wallet(self, _licx: IconScoreBase, _amount: int):
        for i in range(len(self._delegation_address)):
            basis_point = Utils.calcBPS(self.delegation_value[i], _licx._balances[self._address])
            subtract = Utils.calcValueProportionalToBasisPoint(_amount, basis_point)

            self.delegation_value[i] -= subtract
            _licx._delegation[self.delegation_address[i]] -= subtract

            if _licx._delegation[self.delegation_address[i]] <= 0:
                Utils.remove_from_array(_licx._delegation_keys, self.delegation_address[i])
            if self.delegation_value[i] <= 0:
                Utils.remove_from_array(self.delegation_address, self.delegation_address[i])
                Utils.remove_from_array(self.delegation_value, self.delegation_value[i])

    def calc_distribute_delegations(self, _reward: int, _balance: int, _delegations: DictDB):
        for i in range(len(self._delegation_address)):
            basis_point = Utils.calcBPS(self._delegation_value[i], _balance)
            delegation_value = Utils.calcValueProportionalToBasisPoint(_reward, basis_point)
            self._delegation_value[i] += delegation_value
            _delegations[self._delegation_address[i]] += delegation_value

    def has_voting_power(self) -> bool:
        return len(self.delegation_address) > 0

    def exists(self):
        return self.node_id > 0

    @property
    def locked(self) -> int:
        return self._locked.get()

    @locked.setter
    def locked(self, _value):
        self._locked.set(_value)

    @property
    def unstaking(self) -> int:
        return self._unstaking.get()

    @unstaking.setter
    def unstaking(self, _value):
        self._unstaking.set(_value)

    @property
    def join_values(self) -> ArrayDB:
        return self._join_values

    @property
    def leave_values(self) -> ArrayDB:
        return self._leave_values

    @property
    def unlock_heights(self) -> ArrayDB:
        return self._unlock_heights

    @property
    def unstake_heights(self) -> ArrayDB:
        return self._unstake_heights

    @property
    def node_id(self) -> int:
        return self._node_id.get()

    @node_id.setter
    def node_id(self, _value):
        self._node_id.set(_value)

    @property
    def delegation_address(self):
        return self._delegation_address

    @property
    def delegation_value(self):
        return self._delegation_value

    def serialize(self) -> dict:
        return {
            "locked": self.locked,
            "join_values": list(self.join_values),
            "unlock_heights": list(self.unlock_heights),
            "unstaking": self.unstaking,
            "leave_values": list(self.leave_values),
            "unstake_heights": list(self.unstake_heights),
            "delegation_addr": list(self.delegation_address),
            "delegation_values": list(self._delegation_value),
        }

    @property
    def address(self):
        return self._address
