from iconservice import *


class FakeSystemContractInterface(ABC):

    @abstractmethod
    def setStake(self) -> str:
        pass

    @abstractmethod
    def setDelegation(self, params: str):
        pass

    @abstractmethod
    def claimIScore(self):
        pass

    @abstractmethod
    def getStake(self, _account: Address) -> int:
        pass

    @abstractmethod
    def getDelegation(self, _account: Address) -> str:
        pass

    @abstractmethod
    def getTotalSupply(self) -> int:
        pass

    @abstractmethod
    def getDelegationSupply(self) -> int:
        pass

    @abstractmethod
    def getDelegationRate(self) -> int:
        pass

    @abstractmethod
    def queryIScore(self) -> int:
        pass
