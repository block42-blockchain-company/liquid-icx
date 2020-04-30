from iconservice import *

from .consts import *
from .Request import Request
from .irc_2_interface import IRC2TokenStandard
from .token_fallback_interface import TokenFallbackInterface


class LiquidICX(IconScoreBase, IRC2TokenStandard):

    @eventlog(indexed=2)
    def Debug(self, nextPrepTerm: int, blockHeight: int):
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

        self._requests = ArrayDB("requests", db, value_type=Address)

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
        self._balances[self.msg.sender] = total_supply

    def on_update(self) -> None:
        super().on_update()

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

    @payable
    @external(readonly=False)
    def join(self) -> None:
        self._requestJoin()

        # if iss_info["nextPrepTerm"] - iss_info["blockHeight"] < 100:
        #    self._handleRequests()

        self.Join(self.msg.sender, self.msg.value)

    def _requestJoin(self):
        if self.msg.value < 0:
            revert("Joining value cannot be less than zero")

        rq = Request(self.db, self.msg.sender)
        if rq.address is '':
            rq.value = self.msg.value
            rq.address = self.msg.sender
            self._requests.put(self.msg.sender)
        else:
            rq.value = rq.value + self.msg.value

    def _handleRequests(self):
        for it in self._requests:
            rq = Request(self.db, it)
            self.call(FAKE_SYSTEM_CONTRACT_YEIUIDO, "setStake", {}, rq.value)
            self.call(FAKE_SYSTEM_CONTRACT_YEIUIDO, "setDelegation", {"params": "block42"})
            self._mint(rq.value.address, rq.value)

    @external(readonly=True)
    def getRequests(self) -> list:
        response = []
        for rq in self._requests:
            response.append(Request(self.db, rq).serialize())
        return response

    @external(readonly=False)
    def clearRequests(self):
        #Only dev method
        for rq in self._requests:
            Request(self.db, rq).delete()
            self._requests.pop()

    def _transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        # Checks the sending value and balance.
        if _value < 0:
            revert("Transferring value cannot be less than zero")
        if self._balances[_from] < _value:
            revert("Out of balance")

        self._balances[_from] = self._balances[_from] - _value
        self._balances[_to] = self._balances[_to] + _value

        if _to.is_contract:
            # If the recipient is SCORE,
            #   then calls `tokenFallback` to hand over control.
            recipient_score = self.create_interface_score(_to, TokenFallbackInterface)
            recipient_score.tokenFallback(_from, _value, _data)

        # Emits an event log `Transfer`
        self.Transfer(_from, _to, _value, _data)
        Logger.debug(f'Transfer({_from}, {_to}, {_value}, {_data})', TAG)

    @payable
    @external(readonly=False)
    def deposit(self):
        # 1. Stake the ICX in message
        # 2. Vote with ICX
        # 3. Mint
        # TODO Deprected method, we should use create_interface_score
        # https://icon-project.github.io/score-guide/classes.iconscorebase.html#iconservice.iconscore.icon_score_base.IconScoreBase.IconScoreBase.create_interface_score
        self.call(FAKE_SYSTEM_CONTRACT_LOCAL, "setStake", {}, self.msg.value)
        self.call(FAKE_SYSTEM_CONTRACT_LOCAL, "setDelegation", {"params": "block42"})
        self._mint(self.msg.sender, self.msg.value)

    @external(readonly=False)
    def withdraw(self):
        pass

    def _mint(self, _account: Address, _amount: int):
        if _account == ZERO_WALLET_ADDRESS:
            revert("LiquidICX: mint to the zero address")

        self._balances[_account] = self._balances[_account] + _amount
        self._total_supply = self._total_supply + _amount

        self.Transfer(ZERO_WALLET_ADDRESS, _account, _amount, b'None')

    def _burn(self, _account: Address, _amount: int):
        if _account == ZERO_WALLET_ADDRESS:
            revert("LiquidICX: burn from the zero address")
        if self._balances[_account] - _amount < 0:
            revert("LiquidICX: burn amount exceeds balance")

        self._balances[_account] = self._balances[_account] - _amount
        self._total_supply = self._total_supply - _amount

        self.Transfer(_account, ZERO_WALLET_ADDRESS, _amount, b'None')
