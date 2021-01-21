from .scorelib.utils import *

class Wallet:
    __sys_score = IconScoreBase.create_interface_score(SYSTEM_SCORE, InterfaceSystemScore)

    def __init__(self, db: IconScoreDatabase, _address: Address):
        self.__address: Address = _address
        self._locked = VarDB("locked_" + str(_address), db, value_type=int)
        self._unstaking = VarDB("unstaking_" + str(_address), db, value_type=int)

        # Presents how much user deposited to SCORE in chronological order
        self._join_values = ArrayDB("join_values_" + str(_address), db, value_type=int)
        self._unlock_heights = ArrayDB("unlock_heights" + str(_address), db, value_type=int)

        # Presents with how much LICX user wants to leave in chronological order
        self._leave_values = ArrayDB("leave_values" + str(_address), db, value_type=int)
        self._unstake_heights = ArrayDB("unstake_heights" + str(_address), db, value_type=int)

        # Wallet ID in linked list
        self._node_id = VarDB("wallet_id_" + str(_address), db, value_type=int)

        # Tracking individual wallet's delegations
        self._delegation_address = ArrayDB("delegation_addr_" + str(_address), db, value_type=Address)
        self._delegation_value = ArrayDB("delegation_value_" + str(_address), db, value_type=int)

    def join(self, join_amount: int, delegation: dict, licx: IconScoreBase):
        """
        Adds new values to the wallet's join queues
        :param join_amount: amount of ICX that a wallet sent
        :param delegation:
        :param licx
        """

        if len(self._join_values) >= 10:
            revert("LiquidICX: Wallet tries to join more than 10 times in 2 terms. This is considered as spam")

        iiss_info = self.__sys_score.getIISSInfo()

        self._join_values.put(join_amount)
        self._unlock_heights.put(iiss_info["nextPRepTerm"] + TERM_LENGTH)
        self.locked = self.locked + join_amount

        delegation_amount_sum = 0
        prep_list: list = self.__sys_score.getMainPReps()["preps"]
        prep_list.extend(self.__sys_score.getSubPReps()["preps"])
        for address, value in delegation.items():
            prep_address: Address = Address.from_string(address)
            if prep_address in self._delegation_address:
                index = list(self._delegation_address).index(prep_address)
                self._delegation_value[index] += value
                licx.delegation[prep_address] += value
            else:
                if prep_address in licx.delegation_keys:
                    licx.delegation[prep_address] += value
                elif not any(prep['address'] == prep_address for prep in prep_list):
                    revert("LiquidICX: Given address is not a P-Rep.")
                else:
                    licx.delegation_keys.put(prep_address)
                    licx.delegation[prep_address] = value
                self._delegation_address.put(prep_address)
                self._delegation_value.put(value)
            delegation_amount_sum += value

        if delegation_amount_sum != join_amount:
            revert("LiquidICX: Delegations values do not match to the amount of ICX sent.")

    def requestLeave(self, _leave_amount):
        """
        Adds a leave amount to the wallet's leave queue.
        :param _leave_amount: Amount of LICX for a leave request
        """

        if len(self._leave_values) >= 10:
            revert("LiquidICX: Wallet has already 10 leave requests. This is considered a spam")

        self._leave_values.put(_leave_amount)
        self.unstaking = self.unstaking + _leave_amount

    def leave(self) -> int:
        """
        Resolves a leave request.
        It adds an unstaking period for all un-resolved leave requests.
        :return: Sum of newly resolved leave requests
        """

        leave_amount = 0
        if len(self._leave_values) != len(self._unstake_heights):
            current_height = self.__sys_score.getIISSInfo()["blockHeight"]
            unstake_period = self.__sys_score.estimateUnstakeLockPeriod()["unstakeLockPeriod"]

            for it in range(len(self._unstake_heights), len(self._leave_values)):
                leave_amount = leave_amount + self._leave_values[it]
                self._unstake_heights.put(current_height + unstake_period + UNSTAKING_MARGIN)
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

    def exists(self):
        return self.node_id > 0

    def calcDistributeDelegations(self, reward: int, balance: int, delegations: DictDB):
        for i in range(len(self._delegation_address)):
            basis_point = Utils.calcBPS(self._delegation_value[i], balance)
            delegation_value = int((reward * basis_point) / 10000)
            self._delegation_value[i] += delegation_value
            delegations[Address.from_string(self._delegation_address[i])] += delegation_value

    def send(self, _value: int, licx: IconScoreBase):
        for i in range(len(self.delegation_address)):
            basis_point = Utils.calcBPS(self.delegation_value[i], licx._balances[self.__address])
            subtract = int((_value * basis_point) / 10000)
            self.delegation_value[i] -= subtract
            licx.delegation[self.delegation_address[i]] -= subtract

        licx._balances[self.__address] = licx._balances[self.__address] - _value
        if self.exists() and licx._balances[self.__address] < licx._min_value_to_get_rewards.get() and self.locked == 0:
            licx._wallets.remove(self.node_id)
            self.node_id = 0

    def receive(self, _value, licx: IconScoreBase):
        if licx._balances[self.__address] > 0:
            for i in range(len(self.delegation_address)):
                prep_address = self.delegation_address[i]
                delegated_value = self.delegation_value[i]
                basis_point = Utils.calcBPS(delegated_value, licx._balances[self.__address])
                add = int((_value * basis_point) / 10000)
                self.delegation_value[i] += add
                licx.delegation[prep_address] += add
        else:
            for i in licx.delegation_keys:
                basis_point = Utils.calcBPS(licx.delegation[i], licx._total_supply.get())
                value = int((_value * basis_point) / 10000)
                self.delegation_value.put(value)
                self.delegation_address.put(licx.delegation_keys[i])
                licx.delegation[i] += value
        licx._balances[self.__address] = licx._balances[self.__address] + _value
        if not self.exists() and licx._balances[self.__address] >= licx._min_value_to_get_rewards.get():
            node_id = licx._wallets.append(str(self.__address))
            self.node_id = node_id

    @property
    def delegations(self) -> list:
        delegations = []
        for it in range(len(self.delegation_address)):
            delegations.append({
                "address": Address.from_string(self.delegation_address[it]),
                "value": self.delegation_value[it]
            })
        return delegations

    @property
    def locked(self) -> int:
        return self._locked.get()

    @locked.setter
    def locked(self, value):
        self._locked.set(value)

    @property
    def unstaking(self) -> int:
        return self._unstaking.get()

    @unstaking.setter
    def unstaking(self, value):
        self._unstaking.set(value)

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
    def node_id(self, value):
        # if self.node_id != 0 and value != 0:
        #     revert("LiquidICX: The node id was already set.")
        self._node_id.set(value)

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
