from iconservice import *

from .scorelib.consts import *
from .interfaces.irc_2_interface import *
from .interfaces.token_fallback_interface import TokenFallbackInterface
from .scorelib.consts import *


class LiquidICX(IconScoreBase, IRC2TokenStandard):
    # ================================================
    #  Initialization
    # ================================================
    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        # IRC2 Standard variables
        self._total_supply = VarDB('total_supply', db, value_type=int)
        self._decimals = VarDB('decimals', db, value_type=int)
        self._balances = DictDB('balances', db, value_type=int)

        # LICX variables
        # self._wallets = LinkedListDB("wallets", db, str)

        self._min_value_to_get_rewards = VarDB("min_value_to_get_rewards", db, int)

        self._rewards = VarDB("rewards", db, int)
        self._new_unlocked_total = VarDB("new_unlocked_total", db, int)
        self._total_unstake_in_term = VarDB("total_unstake_in_term", db, int)

        self._last_distributed_height = VarDB("last_distributed_height", db, int)

        self._distribute_it = VarDB("distribute_it", db, int)
        self._iteration_limit = VarDB("iteration_limit", db, int)

        self._distributing = VarDB("distributing", db, bool)

        self._cap = VarDB("cap", db, int)

        # System SCORE
        self._system_score = IconScoreBase.create_interface_score(SYSTEM_SCORE, InterfaceSystemScore)

    def on_install(self, _decimals: int = 18) -> None:
        super().on_install()

        if _decimals < 0:
            revert("LiquidICX: Decimals cannot be less than zero")

        self._total_supply.set(0)
        self._decimals.set(_decimals)

        # We do not want to distribute the first < two terms, when SCORE is created
        self._last_distributed_height.set(self._system_score.getIISSInfo()["nextPRepTerm"])

        self._min_value_to_get_rewards.set(10 * 10**_decimals)
        self._iteration_limit.set(500)
        self._distributing.set(False)

        self._cap.set(1000 * 10 ** _decimals)

    def on_update(self) -> None:
        super().on_update()

    # ================================================
    #  External methods
    # ================================================
    @external(readonly=True)
    def name(self) -> str:
        return "LiquidICX"

    @external(readonly=True)
    def symbol(self) -> str:
        return "LICX"

    @external(readonly=True)
    def decimals(self) -> int:
        return self._decimals.get()

    @external(readonly=True)
    def totalSupply(self) -> int:
        return self._total_supply.get()

    @external(readonly=True)
    def balanceOf(self, _owner: Address) -> int:
        return 0

    @external
    def stop(self):
        if self.msg.sender != self.owner:
            revert("LiquidICX: Only owner function at current state.")

        self._system_score.setDelegation([])
        self._system_score.setStake(0)

    @external
    def withdraw(self):
        if self.msg.sender != self.owner:
            revert("LiquidICX: Only owner function at current state.")

        self.icx.send(self.owner, self.icx.get_balance(self.address))


    @external
    def transfer(self, _to: Address, _value: int, _data: bytes = None) -> None:
        """
        External entry function to send LICX from one wallet to another
        :param _to: Recipient's wallet
        :param _value: LICX amount to transfer
        :param _data: Optional information for transfer Event
        """
        revert("LiquidICX: Out-dated contract!")


    @payable
    def fallback(self):
        """
        Called when anyone sends ICX to the SCORE.
        """
        revert('LiquidICX: LICX does not accept ICX. If you want to enter the pool, you need to call "join" method.')

