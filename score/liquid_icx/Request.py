from iconservice import *


class Request:
    def __init__(self, db: IconScoreDatabase, _address: Address):
        self._address = VarDB("rq_address_" + _address.__str__(), db, value_type=str)
        self._value = VarDB("rq_value_" + _address.__str__(), db, value_type=int)


    def delete(self):
        self._address.remove()
        self._value.remove()

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

    def serialize(self) -> dict:
        return {
            "address": self.address,
            "value": self.value
        }
