from iconservice import *
from .consts import *
from .Holder import Holder
from .interfaces.irc_2_interface import *
from .interfaces.token_fallback_interface import *
from .interfaces.system_score_interface import *
from .scorelib.linked_list import *
from .scorelib.Utils import *


class Delegation(TypedDict):
    address: Address
    value: int


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

    @eventlog(indexed=0)
    def Distribute(self):
        pass

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
        self._holders = LinkedListDB("holders_list", db, str)

        self._min_join_value = VarDB("min_join_value", db, int)

        self._rewards = VarDB("rewards", db, int)

        self._last_distributed_height = VarDB("last_distributed_height", db, int)

        self._distribute_it = VarDB("distribute_it", db, int)
        self._iteration_limit = VarDB("iteration_limit", db, int)

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

        self._min_join_value.set(10 * 10 ** _decimals)
        self._iteration_limit.set(500)

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
    def getHolder(self, _address: Address = None) -> dict:
        if self.msg.sender is None:
            revert("LiquidICX: You need to specify the 'from' attribute in your call.")
        return Holder(self.db, self.msg.sender).serialize()  #

    @external(readonly=True)
    def test(self) -> bool:
        return self.msg.sender in self._balances

    @external(readonly=True)
    def getHolders(self) -> list:
        result = []
        for item in self._holders:
            result.append(str(item))
        return result

    @external(readonly=True)
    def getStaked(self) -> dict:
        return IconScoreBase.create_interface_score(ZERO_SCORE_ADDRESS, InterfaceSystemScore).getStake(self.address)

    @external(readonly=True)
    def getDelegation(self) -> dict:
        return IconScoreBase.create_interface_score(ZERO_SCORE_ADDRESS, InterfaceSystemScore).getDelegation(
            self.address)

    @staticmethod
    def linkedlistdb_sentinel(db: IconScoreDatabase, item, **kwargs) -> bool:
        node_id, value = item
        return value == kwargs['match']

    @external(readonly=True)
    def selectFromHolders(self, address: str) -> list:
        return self._holders.select(0, self.linkedlistdb_sentinel, match=address)

    @external(readonly=True)
    def getHolderByNodeID(self, id: int) -> Address:
        return self._holders.node_value(id)

    @external(readonly=False)
    def removeHolder(self) -> None:
        self._burn(self.msg.sender, self._balances[self.msg.sender])
        Holder(self.db, self.msg.sender).delete()
        # Holder.remove_from_array(self._holders, self.msg.sender)

    @external(readonly=False)
    def unlockHolderLicx(self) -> int:
        return Holder(self.db, self.msg.sender).unlock()

    @external(readonly=True)
    def getLocked(self) -> list:
        return list(range(len(Holder(self.db, self.msg.sender).allow_transfer_height)))

    @payable
    @external(readonly=False)
    def join(self) -> None:
        """
        https://github.com/icon-project/icon-service/blob/release/1.7.0/tests/integrate_test/samples/sample_internal_call_scores/sample_system_score_intercall/sample_system_score_intercall.py
        """
        if self.msg.value < 0:
            revert("Joining value cannot be less than zero")

        if self.msg.sender not in self._balances:
            self._holders.append(str(self.msg.sender))

        Holder(self.db, self.msg.sender).update(self.msg.value)
        system_score = Utils.system_score_interface()
        system_score.setStake(self.getStaked()["stake"] + self.msg.value)

        delegation_info: Delegation = {
            "address": Address.from_string("hxec79e9c1c882632688f8c8f9a07832bcabe8be8f"),
            "value": self.getDelegation()["totalDelegated"] + self.msg.value
        }

        system_score.setDelegation([delegation_info])

        self._mint(self.msg.sender, self.msg.value)
        self.Join(self.msg.sender, self.msg.value)

    @external
    def distribute(self):
        """ Distribute I-Score rewards once per term """
        sys_score = Utils.system_score_interface()
        if self._last_distributed_height.get() < sys_score.getPRepTerm()["startBlockHeight"]:
            if self._rewards.get() is 0:
                self._rewards.set(sys_score.claimIScore() / 1000)
                sys_score.setStake(sys_score.getStake(self.address) + self._rewards.get())
                # TODO setDelegate()

            start_it = self._distribute_it.get()
            end_it = self._distribute_it.get() + self._iteration_limit.get()
            for it in range(start_it, end_it):
                holder_address = self._holders.node_value(it)
                holder = Holder(self.db, holder_address)
                holder.unlock()
                if holder.transferable >= 10 ** 18:
                    # update balances, only if User has at least 1 LICX
                    holder_rewards = int(holder.transferable / self._total_supply.get() * self._rewards.get())
                    self._mint(self.msg.sender, holder_rewards, True)
                    holder.transferable += holder_rewards

                if holder_address is self._holders.tail_value():
                    # distribution finished, reset stuff
                    self._rewards.set(0)
                    self._distribute_it.set(0)
                    self._last_distributed_height.set(sys_score.getPRepTerm()["startBlockHeight"])
                    self.Distribute()
                    break

    def leave(self):
        pass

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
            self.Debug("TODO: remove user from holders.")

        if _to not in self._balances:
            self._holders.append(self.msg.sender)

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

    def _mint(self, _account: Address, _amount: int, _internal: bool = False):
        self._balances[_account] = self._balances[_account] + _amount
        self._total_supply.set(self.totalSupply() + _amount)

        if _internal:
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
