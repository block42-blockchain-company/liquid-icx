from iconservice import *
from .consts import *
from .Holder import Holder
from .irc_2_interface import IRC2TokenStandard
from .token_fallback_interface import TokenFallbackInterface


class FakeSystemContractInterface(InterfaceScore):
    @interface
    def setStake(self):
        pass


class LiquidICX(IconScoreBase, IRC2TokenStandard):
    _NEXT_TERM_HEIGHT = 0  # Temp

    @eventlog(indexed=2)
    def Debug(self, int1: int, int2: int):
        pass

    @eventlog(indexed=1)
    def Debug(self, str1: str):
        pass

    @eventlog(indexed=2)
    def Join(self, _from: Address, _value: int):
        pass

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        pass

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._total_supply = VarDB('total_supply', db, value_type=int)
        self._decimals = VarDB('decimals', db, value_type=int)
        self._balances = DictDB('balances', db, value_type=int)

        self._holders = ArrayDB("holders", db, value_type=Address)

    def on_install(self, _next_term_height: int, _initialSupply: int = 0, _decimals: int = 18) -> None:
        super().on_install()
        if _initialSupply < 0:
            revert("Initial supply cannot be less than zero")

        if _decimals < 0:
            revert("Decimals cannot be less than zero")

        total_supply = _initialSupply * 10 ** _decimals
        Logger.debug(f'on_install: total_supply={total_supply}', TAG)

        self._total_supply.set(total_supply)
        self._decimals.set(_decimals)
        self._balances[self.msg.sender] = total_supply

        LiquidICX._NEXT_TERM_HEIGHT = _next_term_height

    def on_update(self, _next_term_height: int) -> None:
        super().on_update()
        LiquidICX._NEXT_TERM_HEIGHT = _next_term_height
        Logger.debug(f'on_update: new_next_term_hegiht={_next_term_height}', TAG)

    @external(readonly=True)
    def nextTerm(self) -> int:
        return LiquidICX._NEXT_TERM_HEIGHT

    @external(readonly=False)
    def setNextTerm(self, _next_term: int):
        LiquidICX._NEXT_TERM_HEIGHT = _next_term

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
        return self._balances[_owner]

    @external
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        if _data is None:
            _data = b'None'
        self._transfer(self.msg.sender, _to, _value, _data)

    @external(readonly=True)
    def getHolders(self) -> dict:
        result = {}
        for hodler in self._holders:
            result[hodler.__str__()] = self._balances[hodler]
        return result

    @external(readonly=True)
    def getHolder(self) -> dict:
        if self.msg.sender is None:
            revert("LiquidICX: You need to specify the 'from' attribute in your call.")
        return Holder(self.db, self.msg.sender).serialize()

    @external(readonly=False)
    def removeHolder(self) -> None:
        self._burn(self.msg.sender, self._balances[self.msg.sender])
        Holder(self.db, self.msg.sender).delete()
        Holder.remove_from_array(self._holders, self.msg.sender)


    @payable
    @external(readonly=False)
    def join(self) -> None:
        if self.msg.value < 0:
            revert("Joining value cannot be less than zero")

        holder = Holder(self.db, self.msg.sender)
        if self.msg.sender not in self._holders:
            holder.create(self.msg.value, self.block_height,
                          LiquidICX._NEXT_TERM_HEIGHT + TERM_LENGTH)
            self._holders.put(self.msg.sender)
        else:
            holder.update(self.msg.value, self.block_height, LiquidICX._NEXT_TERM_HEIGHT + TERM_LENGTH)
        self._mint(self.msg.sender, self.msg.value)

    def _transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        # Checks the sending value and balance.
        if _value < 0:
            revert("LiquidICX: Transferring value cannot be less than zero.")
        if self._balances[_from] < _value:
            revert("LiquidICX: Out of balance")
        if _to == ZERO_WALLET_ADDRESS:
            revert("LiquidICX: Can not transfer LICX to zero wallet address.")

        sender = Holder(self.db, _from)
        receiver = Holder(self.db, _to)

        if not sender.canTransfer(LiquidICX._NEXT_TERM_HEIGHT):
            revert("LiquidICX: You don't have any transferable LICX yet.")

        sender.transferable = sender.transferable - _value
        self._balances[_from] = self._balances[_from] - _value

        if _to not in self._holders:
            self._holders.put(_to)

        receiver.transferable = receiver.transferable + _value
        self._balances[_to] = self._balances[_to] + _value

        if _to.is_contract:
            # If the recipient is SCORE,
            # then calls `tokenFallback` to hand over control.
            recipient_score = self.create_interface_score(_to, TokenFallbackInterface)
            recipient_score.tokenFallback(_from, _value, _data)

        # Emits an event log `Transfer`
        self.Transfer(_from, _to, _value, _data)
        Logger.debug(f'Transfer({_from}, {_to}, {_value}, {_data})', TAG)

    def _mint(self, _account: Address, _amount: int):
        self._balances[_account] = self._balances[_account] + _amount
        self._total_supply.set(self.totalSupply() + _amount)

        self.Transfer(ZERO_WALLET_ADDRESS, _account, _amount, b'None')

    def _burn(self, _account: Address, _amount: int):
        if _account == ZERO_WALLET_ADDRESS:
            revert("LiquidICX: burn from the zero address")
        if self._balances[_account] - _amount < 0:
            revert("LiquidICX: burn amount exceeds balance")

        self._balances[_account] = self._balances[_account] - _amount
        self._total_supply.set(self.totalSupply() - _amount)

        # TODO  Does it make sense to remove here a holder, if balances[owner] == 0 ?

        self.Transfer(_account, ZERO_WALLET_ADDRESS, _amount, b'None')
