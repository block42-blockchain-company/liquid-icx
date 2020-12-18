from .liquid_icx import *
from .scorelib.utils import *


class Wallet:
    __sys_score = IconScoreBase.create_interface_score(SYSTEM_SCORE, InterfaceSystemScore)

    def __init__(self, db: IconScoreDatabase, _address: Address):
        self._locked = VarDB("locked_" + _address.__str__(), db, value_type=int)
        self._unstaking = VarDB("unstaking_" + _address.__str__(), db, value_type=int)

        # Presents how much user deposited to SCORE in chronological order
        self._join_values = ArrayDB("join_values_" + str(_address), db, value_type=int)
        self._unlock_heights = ArrayDB("unlock_heights" + str(_address), db, value_type=int)

        # Presents with how much LICX user wants to leave in chronological order
        self._leave_values = ArrayDB("leave_values" + str(_address), db, value_type=int)
        self._unstake_heights = ArrayDB("unstake_heights" + str(_address), db, value_type=int)

        # Wallet ID in linked list
        self._wallet_id = VarDB("wallet_id_" + str(_address), db, value_type=int)

        # Tracking individual wallet's delegations
        # self._voting = VarDB("voting_" + str(_address), db, value_type=int)
        self._delegation_address = ArrayDB("delegation_addr_" + str(_address), db, value_type=str)
        self._delegation_value = ArrayDB("delegation_value_" + str(_address), db, value_type=int)
        # self._delegation_bps = ArrayDB("delegation_bps_" + str(_address), db, value_type=int)

    def join(self, join_amount: int, delegation: dict):
        """
        Adds new values to the wallet's join queues
        :param voting:
        :param delegation:
        :param join_amount: amount of ICX that a wallet sent
        """

        if len(self._join_values) >= 10:
            revert("LiquidICX: Wallet tries to join more than 10 times in 2 terms. This is considered as spam")

        iiss_info = self.__sys_score.getIISSInfo()

        self._join_values.put(join_amount)
        self._unlock_heights.put(iiss_info["nextPRepTerm"] + TERM_LENGTH)
        self.locked = self.locked + join_amount

        delegation_amount_sum = 0
        for addr, value in delegation.items():
            if addr not in self._delegation_address:
                self._delegation_address.put(addr)
                self._delegation_value.put(value)
            else:
                index = list(self._delegation_address).index(addr)
                self._delegation_value[index] += value
            delegation_amount_sum += value

        Logger.info(f"Total delegation {delegation_amount_sum} : Join amount {join_amount}")
        if delegation_amount_sum != join_amount:
            revert(f"LiquidICX: Delegations values do not match to the amount of ICX sent. {delegation_amount_sum} : {join_amount}")

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

    def changeDelegation(self):
        pass

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
    def node_id(self):
        return self._wallet_id.get()

    @node_id.setter
    def node_id(self, value):
        if self.node_id != 0:
            revert("LiquidICX: The node id was already set.")
        self._wallet_id.set(value)

    # @property
    # def voting(self):
    #     return self._voting.get()
    #
    # @voting.setter
    # def voting(self, voting: int):
    #     self._voting.set(voting)

    @property
    def delegation_address(self):
        return self._delegation_address

    @property
    def delegation_value(self):
        return self._delegation_value

    # @property
    # def delegation_value(self):
    #     return self._delegation_bps

    def serialize(self) -> dict:
        return {
            "locked": self.locked,
            "join_values": list(self.join_values),
            "unlock_heights": list(self.unlock_heights),
            "unstaking": self.unstaking,
            "leave_values": list(self.leave_values),
            "unstake_heights": list(self.unstake_heights),
            # "voting": self.voting,
            "delegation_addr": list(self.delegation_address),
            "delegation_values": list(self._delegation_value),
            # "delegation_bps": list(self._delegation_bps)
        }
