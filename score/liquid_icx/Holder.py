from iconservice import *


class Holder:
    def __init__(self, db: IconScoreDatabase, _address: Address):
        # How much is user allowed to transfer
        # Sum of these two variables should be equal to LiquidICX._balance[user_address]
        # After two terms were passed, locked becomes transferable
        self._transferable = VarDB("transferable_" + _address.__str__(), db, value_type=int)
        self._locked = VarDB("locked_" + _address.__str__(), db, value_type=int)

        # Presents how much user deposited to SCORE in chronological order
        self._join_values = ArrayDB("join_values_" + _address.__str__(), db, value_type=int)
        self._join_height = ArrayDB("join_height_" + _address.__str__(), db, value_type=int)
        self._allow_transfer_height = ArrayDB("allow_transfer_" + _address.__str__(), db, value_type=int)

        # Store in which holders array you can find particular holder
        self._holders_index = VarDB("holders_index" + _address.__str__(), db, value_type=int)

    def update(self, join_details: dict):
        if len(self._join_values) > 10:
            revert("LiquidICX: You can not join as right now. This is considered as spam")

        if join_details["holder_index"] is not None:
            self.holders_index = join_details["holder_index"]

        self._join_values.put(join_details["value"])
        self._join_height.put(join_details["block_height"])
        self._allow_transfer_height.put(join_details["allow_transfer_height"])

        self.locked = self.locked + join_details["value"]

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

        self.holders_index = 0
        self.locked = 0
        self.transferable = 0

    def unlock(self, next_term: int) -> int:
        """
        Unlocks user's LICX and removes entry from the _join_values, join_height, _allow_transfer_height
        :param next_term: Block height of next term
        :return: Amount of new unlocked LICX
        """
        unlocked = 0
        if self.locked > 0:
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
        self.unlock(next_term)
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
    def holders_index(self) -> int:
        return self._holders_index.get()

    @holders_index.setter
    def holders_index(self, value):
        self._holders_index.set(value)

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
            "holders_index": self.holders_index
        }
