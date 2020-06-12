from iconservice import *


class Holder:
    def __init__(self, db: IconScoreDatabase, _address: Address):
        # How much is user allowed to transfer
        # Sum of these two variables should be equal to LiquidICX._balance[user_adress]
        # After two terms were passed, locked becomes transferable
        self._transferable = VarDB("transferable_" + _address.__str__(), db, value_type=int)
        self._locked = VarDB("locked_" + _address.__str__(), db, value_type=int)

        # Presents how much user deposited to SCORE in chronological order
        self._join_values = ArrayDB("join_values_" + _address.__str__(), db, value_type=int)
        self._join_height = ArrayDB("join_height_" + _address.__str__(), db, value_type=int)
        self._allow_transfer_height = ArrayDB("allow_transfer_" + _address.__str__(), db, value_type=int)

    def create(self, _amount, _block_height, _allow_transfer_height):
        # Initialisation of a holder, when he joins the first time
        self._join_values.put(_amount)
        self._join_height.put(_block_height)
        self._allow_transfer_height.put(_allow_transfer_height)

        self.locked = _amount
        # self._transferable.set(0)  # Probably don't need that

    def update(self, _amount, _block_height, _allow_transfer_height):
        self._join_values.put(_amount)
        self._join_height.put(_block_height)
        self._allow_transfer_height.put(_allow_transfer_height)

        self.locked = self.locked + _amount


    def unlock(self):
        pass

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

    def canTransfer(self, next_term: int) -> int:
        if self.locked > 0:
            for it in range(len(self._allow_transfer_height)):
                if next_term > self._allow_transfer_height[it]:
                    # unluck LICX
                    self.locked = self.locked - self._join_values[it]
                    self.transferable = self.transferable + self._join_values[it]

                    self.remove_from_array(self._join_values, self._join_values[it])
                    self.remove_from_array(self._join_height, self._join_height[it])
                    self.remove_from_array(self._allow_transfer_height, self._allow_transfer_height[it])
                else:
                    break

        return self.transferable

    @property
    def transferable(self) -> int:
        return self._transferable.get()

    @transferable.setter
    def transferable(self, value) -> int:
        self._transferable.set(value)

    @property
    def locked(self) -> int:
        return self._locked.get()

    @locked.setter
    def locked(self, value):
        self._locked.set(value)

    @property
    def join_values(self):
        return self._join_values

    @property
    def join_height(self):
        return self._join_height

    @join_height.setter
    def join_height(self, value: int):
        pass

    def serialize(self) -> dict:
        return {
            "transferable": self._transferable.get(),
            "locked": self._locked.get(),
            "join_values": list(self._join_values),
            "join_height": list(self._join_height),
            "allow_transfer_height": list(self._allow_transfer_height)
        }
