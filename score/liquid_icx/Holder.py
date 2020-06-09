from iconservice import *


class Holder:
    def __init__(self, db: IconScoreDatabase, _address: Address):
        # Presents how much user deposited to SCORE in chronological order
        self._join_values = ArrayDB("join_values_" + _address.__str__(), db, value_type=int)
        self._join_height = ArrayDB("join_height_" + _address.__str__(), db, value_type=int)
        self._allow_transfer_height = ArrayDB("allow_transfer_" + _address.__str__(), db, value_type=int)

        # How much is user allowed to transfer
        # Sum of these two variables should be equal to LiquidICX._balance[user_adress]
        # After two terms were passed, locked became transferable
        self._transferable = VarDB("transferable_" + _address.__str__(), db, value_type=int)
        self._locked = VarDB("locked_" + _address.__str__(), db, value_type=int)


    def create(self, msg, block_height, allow_transfer_height):
        # Initiliation of a holder, when he joins the first time
        # self.address = msg.sender
        self._join_values.put(msg.value)
        self._join_height.put(block_height)
        self._allow_transfer_height.put(allow_transfer_height)

        self._locked = msg.value

    def unlock(self, indices_to_delete):
        # I should just probably shift elements to left here
        pass

    def remove_from_array(self, array: ArrayDB, el) -> None:
        temp = []
        # find that element and remove it
        while array:
            current = array.pop()
            if current == el:
                break
            else:
                temp.append(current)
        # append temp back to array
        while temp:
            array.put(temp.pop())



    def delete(self):
        pass


    def canTransfer(self, next_term: int) -> int:
        indices = list()
        for it in range(len(self._allow_transfer_height)):
            if next_term > self._allow_transfer_height[it]:
                indices.append(it)
            else:
                break

        if len(indices):
            self.unlock(indices)

        return self._transferable.get()

    @property
    def join_values(self):
        return self._join_values.get()

    @property
    def join_height(self):
        return self._join_height.get()

    @join_height.setter
    def join_height(self, value: int):
        pass
        # self._join_height.set(value)

    def serialize(self) -> dict:
        return {
            # "address": self.address,
            # "value": self.value
        }
