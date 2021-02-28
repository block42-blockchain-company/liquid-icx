from iconservice import *
from .interfaces.LICXInterface import *





class JoinScore(IconScoreBase):
    """
    This score is used for testing purposes, to test if the SCORE is also able to join the licx protocol.
    """
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
