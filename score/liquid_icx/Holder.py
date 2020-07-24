from .liquid_icx import *


class SystemContractInterface(InterfaceScore):
    @interface
    def getIISSInfo(self):
        pass


class Holder:
    def __init__(self, db: IconScoreDatabase, _address: Address):
        # How much is user allowed to transfer
        # Sum of these two variables should be equal to LiquidICX._balance[user_address]
        # After two terms were passed, locked becomes transferable
        self._transferable = VarDB("transferable_" + str(_address), db, value_type=int)
        self._locked = VarDB("locked_" + _address.__str__(), db, value_type=int)

        # Presents how much user deposited to SCORE in chronological order
        self._join_values = ArrayDB("join_values_" + str(_address), db, value_type=int)
        self._join_height = ArrayDB("join_height_" + str(_address), db, value_type=int)
        self._allow_transfer_height = ArrayDB("allow_transfer_" + str(_address), db, value_type=int)

    def update(self, join_amount: int):
        if len(self._join_values) > 10:
            revert("LiquidICX: You can not join as right now. This is considered as spam")

        system_score = IconScoreBase.create_interface_score(ZERO_SCORE_ADDRESS, SystemContractInterface)
        iiss_info = system_score.getIISSInfo()

        self._join_values.put(join_amount)
        self._join_height.put(iiss_info["blockHeight"])
        self._allow_transfer_height.put(iiss_info["nextPRepTerm"] + TERM_LENGTH)

        self.locked = self.locked + join_amount

    @staticmethod
    def remove_from_array(array: ArrayDB, el) -> None:
        temp = []
        # find that element and remove it
        while array:
            current = array.pop()
            if current == el:
                break
            else:
                temp.append(current)
        # append temp back to arrayDB
        while temp:
            array.put(temp.pop())

    def delete(self):
        while self._join_values:
            self._join_values.pop()
            self._join_height.pop()
            self._allow_transfer_height.pop()

        self.locked = 0
        self.transferable = 0

    def unlock(self, ) -> int:
        """
        Unlocks user's LICX and removes entry from the _join_values, join_height, _allow_transfer_height
        :return: Amount of new unlocked LICX
        """
        unlocked = 0
        if self.locked > 0:
            next_term = LiquidICX.IISSSInfo()["nextPRepTerm"]
            while self._allow_transfer_height:
                if next_term > self._allow_transfer_height[0]:  # always check and remove the first element only
                    self.locked = self.locked - self._join_values[0]
                    self.transferable = self.transferable + self._join_values[0]

                    unlocked += self._join_values[0]

                    self.remove_from_array(self._join_values, self._join_values[0])
                    self.remove_from_array(self._join_height, self._join_height[0])
                    self.remove_from_array(self._allow_transfer_height, self._allow_transfer_height[0])
                else:
                    break
        return unlocked

    def canTransfer(self, next_term: int) -> int:
        self.unlock()
        return self.transferable

    @property
    def transferable(self) -> int:
        return self._transferable.get()

    @transferable.setter
    def transferable(self, value):
        self._transferable.set(value)

    @property
    def locked(self) -> int:
        return self._locked.get()

    @locked.setter
    def locked(self, value):
        self._locked.set(value)

    @property
    def join_values(self) -> ArrayDB:
        return self._join_values

    @property
    def join_height(self) -> ArrayDB:
        return self._join_height

    @property
    def allow_transfer_height(self) -> ArrayDB:
        return self._allow_transfer_height

    def serialize(self) -> dict:
        return {
            "transferable": self.transferable,
            "locked": self.locked,
            "join_values": list(self.join_values),
            "join_height": list(self.join_height),
            "allow_transfer_height": list(self._allow_transfer_height),
        }
