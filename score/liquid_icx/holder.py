from .liquid_icx import *
from .interfaces.system_score_interface import InterfaceSystemScore
from .scorelib.utils import *


class Holder:
    def __init__(self, db: IconScoreDatabase, _address: Address):
        self._locked = VarDB("locked_" + _address.__str__(), db, value_type=int)
        self._claimableICX = VarDB("claimableICX_" + _address.__str__(), db, value_type=int)

        # Presents how much user deposited to SCORE in chronological order
        self._join_values = ArrayDB("join_values_" + str(_address), db, value_type=int)
        self._unlock_heights = ArrayDB("unlock_heights" + str(_address), db, value_type=int)

        self._leave_values = ArrayDB("leave_values" + str(_address), db, value_type=int)
        self._unstake_heights = ArrayDB("unstake_heights" + str(_address), db, value_type=int)

        # Holders ID
        self._node_id = VarDB("holder_id_" + str(_address), db, value_type=int)

    def join(self, join_amount: int, node_id: int = None):
        """
        Adds new values to the wallet's join queues
        :param node_id: Id in holder linked list
        :param join_amount: amount of ICX that a wallet sent
        """

        if len(self._join_values) >= 10:
            revert("LiquidICX: Wallet tries to join more than 10 times in 2 terms. This is considered as spam")

        if self.node_id == 0:
            self._node_id.set(node_id)

        iiss_info = Utils.system_score_interface().getIISSInfo()

        self._join_values.put(join_amount)
        self._unlock_heights.put(iiss_info["nextPRepTerm"] + TERM_LENGTH)

        self.locked = self.locked + join_amount

    def requestLeave(self, _leave_value):
        if len(self._leave_values) >= 10:
            revert("LiquidICX: Wallet has already 10 leave requests. This is considered as spam")

        self._leave_values.put(_leave_value)

    def leave(self) -> int:
        leave = 0
        if len(self._leave_values):
            block_height = Utils.system_score_interface().getIISSInfo()["blockHeight"]
            unstake_period = Utils.system_score_interface().estimateUnstakeLockPeriod()["unstakeLockPeriod"]

            for it in self.leave_values:
                leave = leave + it
                self._unstake_heights.put(block_height + unstake_period)

        return leave

    def unlock(self) -> int:
        """
        Unlocks user's LICX and removes entry from the _join_values, _allow_transfer_height
        :return: Amount of new unlocked LICX
        """

        unlocked = 0
        if self.locked > 0:
            next_term = Utils.system_score_interface().getIISSInfo()["nextPRepTerm"]
            while self._unlock_heights:
                if next_term > self._unlock_heights[0]:  # always check and remove the first element only
                    self.locked = self.locked - self._join_values[0]

                    unlocked += self._join_values[0]

                    Utils.remove_from_array(self._join_values, self._join_values[0])
                    Utils.remove_from_array(self._unlock_heights, self._unlock_heights[0])
                else:
                    break
        return unlocked

    def claim(self):
        if len(self._unlock_heights):
            block_height = Utils.system_score_interface().getIISSInfo()["blockHeight"]
            while self._unstake_heights:
                if block_height > self._unstake_heights[0]:
                    self.claimableICX = self.claimableICX + self._leave_values[0]

                    Utils.remove_from_array(self._leave_values, self._leave_values[0])
                    Utils.remove_from_array(self._unstake_heights, self._unstake_heights[0])
                else:
                    break

    @property
    def locked(self) -> int:
        return self._locked.get()

    @locked.setter
    def locked(self, value):
        self._locked.set(value)

    @property
    def claimableICX(self) -> int:
        return self._claimableICX.get()

    @claimableICX.setter
    def claimableICX(self, value):
        self._claimableICX.set(value)

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
        return self._node_id.get()

    @node_id.setter
    def node_id(self, value):
        self._node_id.set(value)

    def serialize(self) -> dict:
        return {
            "locked": self.locked,
            "join_values": list(self.join_values),
            "unlock_heights": list(self.unlock_heights),
            "leave_values": list(self.leave_values),
            "unstake_heights": list(self.unstake_heights)
        }
