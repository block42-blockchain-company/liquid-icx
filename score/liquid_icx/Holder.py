from iconservice import *


class Holder:
    def __init__(self, db: IconScoreDatabase, _address: Address):
        self._address = VarDB("rq_address_" + _address.__str__(), db, value_type=str)
        self._value = VarDB("rq_value_" + _address.__str__(), db, value_type=int)
        self._join_height = VarDB("join_height_" + _address.__str__(), db, value_type=int)


    def create(self, msg):
        ## Initiliation of a holder, when he joins the first time
        pass

    def delete(self):
        self._address.remove()
        self._value.remove()

    def canTransfer(self, next_term: int) -> bool:
        return self._join_height.get() < next_term

    @property
    def address(self):
        return self._address.get()

    @address.setter
    def address(self, address: Address):
        self._address.set(address.__str__())

    @property
    def value(self):
        return self._value.get()

    @value.setter
    def value(self, value: int):
        self._value.set(value)

    @property
    def join_height(self):
        return self._join_height.get()

    @join_height.setter
    def join_height(self, value: int):
        self._join_height.set(value)


    def serialize(self) -> dict:
        return {
            "address": self.address,
            "value": self.value
        }
