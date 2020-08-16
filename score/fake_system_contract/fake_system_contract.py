from iconservice import *

TAG = 'FakeSystemContract'
TERM_LENGTH = 43120
FIRST_TERM = TERM_LENGTH


class Delegation(TypedDict):
    address: Address
    value: int


class FakeSystemContract(IconScoreBase):
    @eventlog
    def IScoreClaimed(self, iscore: int, icx: int):
        pass

    @eventlog(indexed=1)
    def IScoreClaimedV2(self, address: Address, iscore: int, icx: int):
        pass

    @eventlog
    def PRepRegistered(self, address: Address):
        pass

    @eventlog
    def PRepUnregistered(self, address: Address):
        pass

    @eventlog
    def PRepSet(self, address: Address):
        pass

    def __init__(self, db: 'IconScoreDatabase') -> None:
        super().__init__(db)
        self._termStartHeight = VarDB('term_start_height', db, value_type=int)
        self._stake = VarDB('stake', db, value_type=int)
        self._delegation = VarDB('delegation', db, value_type=int)

    def on_install(self) -> None:
        super().on_install()
        self._termStartHeight.set(FIRST_TERM)

    def on_update(self) -> None:
        super().on_update()

    @external
    def setStake(self, value: int = 0) -> None:
        self._stake.set(value)

    @external(readonly=True)
    def getStake(self, address: Address) -> dict:
        return {
            "stake": hex(self._stake.get())
        }

    @external
    def setDelegation(self, delegations: List[Delegation] = None) -> None:
        delegation = delegations[0]
        self._delegation.set(delegation["value"])

    @external(readonly=True)
    def getDelegation(self, address: Address) -> dict:
        return {
            "totalDelegated": hex(self._delegation.get())
        }

    @external
    def claimIScore(self) -> None:
        pass

    @external(readonly=True)
    def queryIScore(self, address: Address) -> dict:
        return {
            "estimatedICX": hex(int(self._delegation.get() / 10))
        }

    @external(readonly=True)
    def estimateUnstakeLockPeriod(self) -> dict:
        return {}

    @external(readonly=True)
    def getTermStartHeight(self) -> int:
        return self._termStartHeight.get()

    @external
    def incrementTerm(self) -> None:
        current_start_height = self._termStartHeight.get()
        self._termStartHeight.set(current_start_height + TERM_LENGTH)

    @external(readonly=True)
    def getIISSInfo(self) -> dict:
        return {
            "blockHeight": "0xa59",
            "variable": {
                "irep": "0xa968163f0a57b400000",
                "rrep": "0x499"
            },
            "nextCalculation": "0xa5e",
            "nextPRepTerm": hex(self._termStartHeight.get() + TERM_LENGTH),
            "rcResult": {
                "iscore": "0x25ae31ebace4822a50b",
                "estimatedICX": "0x9a56d092205400ad",
                "startBlockHeight": "0xa54",
                "endBlockHeight": "0xa58",
                "stateHash": "0x9fe3640299c522648d177775982d783772ebc8cc37af5e19b68b340f2d6cc60b0ef870590c2dda4f742c1c466ab4aec125d257399cc8165d483b3b59eafc1c02"
            }
        }

    @external(readonly=True)
    def getPRep(self, address: Address) -> dict:
        return {}

    @external(readonly=True)
    def getPReps(self, startRanking: int = None, endRanking: int = None) -> list:
        return []

    @external(readonly=True)
    def getMainPReps(self) -> dict:
        return {}

    @external(readonly=True)
    def getSubPReps(self) -> dict:
        return {}

    @external(readonly=True)
    def getPRepTerm(self) -> dict:
        return {
            "startBlockHeight": hex(self._termStartHeight.get()),
            "endBlockHeight": hex(self._termStartHeight.get() + TERM_LENGTH - 1)
        }

    @external(readonly=True)
    def getInactivePReps(self) -> dict:
        return {}

    @external(readonly=True)
    def getScoreDepositInfo(self, address: Address) -> dict:
        return {}

