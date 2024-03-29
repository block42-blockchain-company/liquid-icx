from iconservice import *
from .interfaces.LICXInterface import *


# ------------------------------------------------------------------
# Bicon test-net address: cxdda1febec68c13ea4e017afc8977bccc12aab4d8
# ------------------------------------------------------------------

class JoinScore(IconScoreBase):

    def Join(self):
        pass

    def Leave(self):
        pass

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self.licx_address = VarDB("licx_address", db, str)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external
    def getLICXAddress(self) -> str:
        return self.licx_address.get()

    @external(readonly=False)
    def setLICXAddress(self, address: str):
        self.licx_address.set(address)

    @payable
    @external(readonly=False)
    def joinLICX(self):
        if self.licx_address == "":
            revert("Set address first")

        self.call(Address.from_string(self.licx_address.get()), "join", {}, self.msg.value)
        self.Join()

    @external(readonly=False)
    def leaveLICX(self):
        if self.licx_address == "":
            revert("Set address first")

        self.create_interface_score(Address.from_string(self.licx_address.get()), LICXInterface).leave()
        self.Leave()
