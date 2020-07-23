from iconservice import *
from .consts import *
from .Holder import Holder
from .interfaces.irc_2_interface import *
from .interfaces.token_fallback_interface import *
from .interfaces.system_contract_interface import *
from .scorelib.linked_list import *


class FakeSystemContractInterface(InterfaceScore):
    @interface
    def setStake(self):
        pass


class LiquidICX(IconScoreBase, IRC2TokenStandard):
    # ================================================
    #  Event logs
    # ================================================
    @eventlog(indexed=2)
    def DebugInt(self, int1: int, int2: int):
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

    # ================================================
    #  Initialization
    # ================================================
    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._total_supply = VarDB('total_supply', db, value_type=int)
        self._decimals = VarDB('decimals', db, value_type=int)
        self._balances = DictDB('balances', db, value_type=int)

        self._holders = LinkedListDB("holders_list", db, Address)

    def on_install(self, _initialSupply: int = 0, _decimals: int = 18) -> None:
        super().on_install()
        if _initialSupply < 0:
            revert("Initial supply cannot be less than zero")

        if _decimals < 0:
            revert("Decimals cannot be less than zero")

        total_supply = _initialSupply * 10 ** _decimals
        Logger.debug(f'on_install: total_supply={total_supply}', TAG)

        self._total_supply.set(total_supply)
        self._decimals.set(_decimals)

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
        return self._balances[_owner]

    @external
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        if _data is None:
            _data = b'None'
        self._transfer(self.msg.sender, _to, _value, _data)

    @external(readonly=True)
    def getHolder(self) -> dict:
        if self.msg.sender is None:
            revert("LiquidICX: You need to specify the 'from' attribute in your call.")
        return Holder(self.db, self.msg.sender).serialize()

    @external(readonly=True)
    def getHolders(self) -> list:
        return self._holders.select(0)

    @external(readonly=False)
    def removeHolder(self) -> None:
        self._burn(self.msg.sender, self._balances[self.msg.sender])
        Holder(self.db, self.msg.sender).delete()
        # Holder.remove_from_array(self._holders, self.msg.sender)

    @external(readonly=False)
    def unlockHolderLicx(self) -> int:
        Holder(self.db, self.msg.sender).unlock()

    @external(readonly=True)
    def getLocked(self) -> list:
        return list(range(len(Holder(self.db, self.msg.sender).allow_transfer_height)))

    @payable
    @external(readonly=False)
    def join(self) -> None:
        if self.msg.value < 0:
            revert("Joining value cannot be less than zero")

        if self.msg.sender not in self._balances:
            self._holders.append(self.msg.sender)
            self.Debug(str(Address))

        Holder(self.db, self.msg.sender).update(self.msg.value)

        self._mint(self.msg.sender, self.msg.value)
        self.Join(self.msg.sender, self.msg.value)

    # ================================================
    #  Internal methods
    # ================================================
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

        if len(sender.join_values):
            sender.unlock()

        if not sender.transferable:
            revert("LiquidICX: You don't have any transferable LICX yet.")

        sender.transferable = sender.transferable - _value
        self._balances[_from] = self._balances[_from] - _value

        if sender.transferable == 0 and sender.locked == 0:
            # remove from holders array
            pass

        if _to not in self._balances:
            self._add_address_to_holders_array(_to)

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
