from iconservice import *

TAG = 'FakeSystemContract'


class FakeSystemContract(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._stake = DictDB('stake', db, value_type=int)
        self._delegation = DictDB('delegation', db, value_type=str)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=False)
    @payable
    def setStake(self) -> str:
        if self.msg.value <= 0:
            revert("FakeSystemContract: Failed to stake. Values is <= 0")

        self._balances[self.msg.sender] += self.msg.value

    @external(readonly=False)
    def setDelegation(self, params: str):
        self._delegation[self.msg.sender.__str__()] = params

    @external(readonly=False)
    def claimIScore(self):
        pass

    @external(readonly=True)
    def getStake(self, _account: Address) -> int:
        return self._stake[_account.__str__()]

    @external(readonly=True)
    def getDelegation(self, _account: Address) -> str:
        return self._delegation[_account.__str__()]

    @external(readonly=True)
    def getTotalSupply(self) -> int:
        return 800460000

    @external(readonly=True)
    def getDelegationSupply(self) -> int:
        return 160092000

    @external(readonly=True)
    def getDelegationRate(self) -> int:
        return (self.getDelegationSupply() / self.getTotalSupply()) * 10 ** 18

    @external(readonly=True)
    def queryIScore(self) -> int:
        pass
