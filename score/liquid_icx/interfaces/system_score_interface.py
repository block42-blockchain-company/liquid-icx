from iconservice import *


class InterfaceSystemScore(InterfaceScore):
    @interface
    def setStake(self, value: int) -> None: pass

    @interface
    def getStake(self, address: Address) -> dict: pass

    @interface
    def estimateUnstakeLockPeriod(self) -> dict: pass

    @interface
    def setDelegation(self, delegations: list = None): pass

    @interface
    def getDelegation(self, address: Address) -> dict: pass

    @interface
    def claimIScore(self): pass

    @interface
    def queryIScore(self, address: Address) -> dict: pass

    @interface
    def getIISSInfo(self) -> dict: pass

    @interface
    def getPRep(self, address: Address) -> dict: pass

    @interface
    def getPReps(self, startRanking: int, endRanking: int) -> list: pass

    @interface
    def getMainPReps(self) -> dict: pass

    @interface
    def getSubPReps(self) -> dict: pass

    @interface
    def getPRepTerm(self) -> dict: pass

    @interface
    def getInactivePReps(self) -> dict: pass

    @interface
    def getScoreDepositInfo(self, address: Address) -> dict: pass