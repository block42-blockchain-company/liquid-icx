from iconservice import *
from .scorelib.consts import *
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
    def Distribute(self, _block_height: int):
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
        self._holders = LinkedListDB("holders", db, str)

        self._min_value_to_get_rewards = VarDB("min_join_value", db, int)

        self._rewards = VarDB("rewards", db, int)

        self._last_distributed_height = VarDB("last_distributed_height", db, int)

        self._distribute_it = VarDB("distribute_it", db, int)
        self._iteration_limit = VarDB("iteration_limit", db, int)

        # System SCORE
        self._system_score = IconScoreBase.create_interface_score(SYSTEM_SCORE, InterfaceSystemScore)

    def on_install(self, _decimals: int = 18) -> None:
        super().on_install()

        if _decimals < 0:
            revert("Decimals cannot be less than zero")

        Logger.debug(f'on_install: total_supply=0', TAG)

        self._total_supply.set(0)
        self._decimals.set(_decimals)

        self._min_value_to_get_rewards.set(10 * 10 ** _decimals)
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

    @external(readonly=True)
    def transferableOf(self, _owner: Address) -> int:
        return Holder(self.db, _owner).transferable

    @external(readonly=True)
    def lockedOf(self, _owner: Address) -> int:
        return Holder(self.db, _owner).locked

    @external
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        if _data is None:
            _data = b'None'
        self._transfer(self.msg.sender, _to, _value, _data)

    @external(readonly=True)
    def getHolder(self, _address: Address = None) -> dict:
        if _address is None:
            revert("LiquidICX: You need to specify the '_address' in your call.")
        return Holder(self.db, _address).serialize()

    @external(readonly=True)
    def getHolders(self) -> list:
        # TODO: Implement with new signature
        # def getHolder(self, start: n_id | Address = None, offset: int) -> list
        result = []
        for item in self._holders:
            result.append(item)
        return result

    @external(readonly=True)
    def getStaked(self) -> dict:
        return self._system_score.getStake(self.address)

    @external(readonly=True)
    def rewards(self) -> int:
        return self._rewards.get()

    @external(readonly=True)
    def getDelegation(self) -> dict:
        return self._system_score.getDelegation(self.address)

    @external(readonly=True)
    def getIterationLimit(self) -> int:
        return self._iteration_limit.get()

    @external(readonly=False)
    def setIterationLimit(self, _value: int):
        if self.msg.sender == self.owner:
            self._iteration_limit.set(_value)
        else:
            revert("LiquidICX: Only owner function at current state.")

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

    @external
    def unlockLicx(self, address: Address = None) -> int:
        if address is None:
            address = self.msg.sender
        return Holder(self.db, address).unlock()

    @payable
    @external
    def join(self) -> None:
        if self.msg.value < self._min_value_to_get_rewards.get():
            revert("Joining value cannot be less than the minimum join value")
        self._join(self.msg.sender, self.msg.value)

    @external
    def distribute(self):
        """ Distribute I-Score rewards once per term """
        if not len(self._holders):
            revert("LiquidICX: No LICX holders.")
        if self._last_distributed_height.get() < self._system_score.getPRepTerm()["startBlockHeight"]:
            if self._rewards.get() == 0:
                # claim rewards and re-stake and re-delegate with these
                self._rewards.set(self._system_score.queryIScore(self.address)["estimatedICX"])
                self._system_score.claimIScore()
                self._system_score.setStake(self._system_score.getStake(self.address)["stake"] + self._rewards.get())
                delegation: Delegation = {
                    "address": Address.from_string("hxec79e9c1c882632688f8c8f9a07832bcabe8be8f"),
                    "value": self.getDelegation()["totalDelegated"] + self._rewards.get()
                }
                self._system_score.setDelegation([delegation])
                # get head id for start iteration
                self._distribute_it.set(self._holders.get_head_node().id)

            it = 0
            cur_id = self._distribute_it.get()
            while cur_id is not None:
                try:
                    cur_address = self._holders.node_value(cur_id)
                    holder = Holder(self.db, cur_address)
                    if holder.transferable >= 10 ** 18:
                        # update balances, only if User has at least 1 LICX
                        holder_rewards = int(holder.transferable / self._total_supply.get() * self._rewards.get())
                        self._mint(self.msg.sender, holder_rewards, True)
                        holder.transferable += holder_rewards
                    if cur_id == self._holders.get_tail_node().id:
                        # distribution finished, reset stuff
                        self._rewards.set(0)
                        self._distribute_it.set(0)
                        self._last_distributed_height.set(self._system_score.getPRepTerm()["startBlockHeight"])
                        self.Distribute(self.block_height)
                        break
                    if it >= self._iteration_limit.get():
                        # save iterator for next distribution call
                        self._distribute_it.set(cur_id)
                        break
                    cur_id = self._holders.next(cur_id)
                    it += 1
                except LinkedNodeNotFound:
                    self.Debug(f"Node with id {cur_id} does not exist.")
                except StopIteration:
                    self.Debug("Something went terrible wrong. This should never happen")
        else:
            revert("LiquidICX: Distribute called already this term.")

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

        if sender.transferable < self._min_value_to_get_rewards.get() and sender.locked == 0:
            self.Debug("TODO: remove user from holders.")

        if _to not in self._balances:
            self._holders.append(_to)

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

    def _join(self, sender: Address, value: int) -> None:
        if sender not in self._balances:
            self._holders.append(str(sender))

        Holder(self.db, sender).update(value)
        system_score = Utils.system_score_interface()
        system_score.setStake(self.getStaked()["stake"] + value)

        delegation_info: Delegation = {
            "address": Address.from_string("hxec79e9c1c882632688f8c8f9a07832bcabe8be8f"),
            "value": self.getDelegation()["totalDelegated"] + value
        }

        system_score.setDelegation([delegation_info])

        self._mint(sender, value)
        self.Join(sender, value)
