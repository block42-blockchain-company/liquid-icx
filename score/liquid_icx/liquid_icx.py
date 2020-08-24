from iconservice import *

from .scorelib.consts import *
from .holder import Holder
from .interfaces.irc_2_interface import *
from .interfaces.token_fallback_interface import TokenFallbackInterface
from .scorelib.linked_list import *
from .scorelib.utils import *



class LiquidICX(IconScoreBase, IRC2TokenStandard):
    # ================================================
    #  Event logs
    # ================================================
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

        self._min_value_to_get_rewards = VarDB("min_value_to_get_rewards", db, int)

        self._rewards = VarDB("rewards", db, int)
        self._new_unlocked_total = VarDB("new_unlocked_total", db, int)

        self._total_unstake_in_term = VarDB("_total_unstake_in_term", db, int)

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

        # We do not want to distribute the first < two terms, when SCORE is created
        self._last_distributed_height.set(self._system_score.getIISSInfo()["nextPRepTerm"])

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
    def lockedOf(self, _owner: Address) -> int:
        return Holder(self.db, _owner).locked

    @external(readonly=True)
    def getHolder(self, _address: Address = None) -> dict:
        if _address is None:
            revert("LiquidICX: You need to specify the '_address' in your call.")
        return Holder(self.db, _address).serialize()

    @external(readonly=True)
    def getHolders(self) -> list:
        result = []
        for item in self._holders:
            result.append(item[1])
        return result

    @external(readonly=True)
    def getStaked(self) -> int:
        return self._system_score.getStake(self.address)["stake"]

    @external(readonly=True)
    def rewards(self) -> int:
        return self._rewards.get()

    @external(readonly=True)
    def getDelegation(self) -> dict:
        return self._system_score.getDelegation(self.address)

    @external(readonly=True)
    def getIterationLimit(self) -> int:
        return self._iteration_limit.get()

    @external(readonly=True)
    def selectFromHolders(self, address: str) -> list:
        return self._holders.select(0, self.linkedlistdb_sentinel, match=address)

    @external(readonly=True)
    def getHolderByNodeID(self, id: int) -> Address:
        return self._holders.node_value(id)

    @external
    def transfer(self, _to: Address, _value: int, _data: bytes = None) -> None:
        """
        External entry function to send LICX from one wallet to another
        :param _to: Recipient's wallet
        :param _value: LICX amount to transfer
        :param _data: Optional information for transfer Event
        """

        if _data is None:
            _data = b'None'
        self._transfer(self.msg.sender, _to, _value, _data)

    @external
    def setIterationLimit(self, _iteration_limit: int) -> None:
        """
        Sets the max number of loops in distribute function
        :param _iteration_limit: Number of iterations
        """

        if self.msg.sender != self.owner:
            revert("LiquidICX: Only owner function at current state.")
        if _iteration_limit <= 0:
            revert("LiquidICX: 'iteration limit' has to be > 0.")

        self._iteration_limit.set(_iteration_limit)

    @staticmethod
    def linkedlistdb_sentinel(db: IconScoreDatabase, item, **kwargs) -> bool:
        """

        :param db: SCORE's db instance
        :param item:
        :param kwargs:
        :return: True if a match was found
        """

        node_id, value = item
        return value == kwargs['match']

    @payable
    @external
    def join(self) -> None:
        """
        External entry point to join the LICX pool
        """

        if self.msg.value < self._min_value_to_get_rewards.get():
            revert("Joining value cannot be less than the minimum join value")
        self._join(self.msg.sender, self.msg.value)

    @external
    def leave(self, _value: int = None) -> None:
        """
        External entry point to leave the LICX pool
        """
        # if not Holder(self.db, self.msg.sender).transferable:
        #    revert("LiquidICX: You don't have any transferable LICX")

        self._leave(self.msg.sender, _value)

    @external
    def distribute(self) -> None:
        """
        Distribute I-Score rewards once per term.
        Iterate over all wallets >= self._min_value_to_get_rewards and give them their reward share.
        This function has to be called multiple times until we iterated over all wallets >= self._min_value_to_get_rewards.
        """

        if not len(self._holders):
            revert("LiquidICX: No holders.")

        if self._last_distributed_height.get() < self._system_score.getPRepTerm()["startBlockHeight"]:
            if not self._rewards.get():
                self._claimRewards()
                # get head id for start iteration
                self._distribute_it.set(self._holders.get_head_node().id)

            cur_id = self._distribute_it.get()
            for it in range(self._iteration_limit.get()):
                cur_address = self._holders.node_value(cur_id)
                holder = Holder(self.db, cur_address)
                # Distribute only to address which have already the LICX unlocked ( more than 2 terms )
                # We decided to distribute only to wallets which have at least 10 LICX, to avoid spam/attacks.
                holder_rewards = 0
                holder_balance = self._balances[Address.from_string(cur_address)]
                if holder_balance >= self._min_value_to_get_rewards.get() and self._total_supply.get():
                    # Reward formula:
                    holder_rewards = int(holder_balance / self._total_supply.get() * self._rewards.get())
                    holder_balance += holder_rewards

                # After distribution the address will unlock LICX, if they have any and update the balances[holder]
                holder_unlocked = holder.unlock()
                self._new_unlocked_total.set(self._new_unlocked_total.get() + holder_unlocked)
                self._balances[Address.from_string(cur_address)] = \
                    self._balances[Address.from_string(cur_address)] + holder_unlocked + holder_rewards

                self._total_unstake_in_term.set(self._total_unstake_in_term.get() + holder.leave())

                if cur_id == self._holders.get_tail_node().id:
                    self._redelegate()
                    self._endDistribution()
                    return
                cur_id = self._holders.next(cur_id)
                # zbrisi iz holderjov, ce je transferable == 0
            self._distribute_it.set(cur_id)
        else:
            revert("LiquidICX: Distribute was already called this term.")

    # ================================================
    #  Internal methods
    # ================================================
    def _claimRewards(self):
        """
        Claim IScore rewards. It is called only once per term, at the start of the cycle.
        """
        self._rewards.set(self._system_score.queryIScore(self.address)["estimatedICX"])
        self._system_score.claimIScore()

    def _redelegate(self):
        """
        Re-stake and re-delegate with the rewards claimed at the start of the cycle.
        """
        restake_value = self.getStaked() + self._rewards.get() - self._total_unstake_in_term.get()
        self._system_score.setStake(restake_value)
        delegation: Delegation = {
            "address": PREP_ADDRESS,
            "value": restake_value
        }
        self._system_score.setDelegation([delegation])

    def _endDistribution(self):
        """
        The function sets the following VarDB to the default state and updates the total supply of LICX.
        """

        self._total_supply.set(self.totalSupply() + self._rewards.get() + self._new_unlocked_total.get())
        self._rewards.set(0)
        self._new_unlocked_total.set(0)
        self._distribute_it.set(0)
        self._last_distributed_height.set(self._system_score.getPRepTerm()["startBlockHeight"])
        self.Distribute(self.block_height)

    def _join(self, sender: Address, value: int) -> None:
        """
        Add a wallet to the LICX pool and issue LICX to it
        :param sender: Wallet that wants to join
        :param value: Amount of ICX to join the pool
        """

        node_id = None
        holder = Holder(self.db, sender)
        if holder.node_id == 0:
            node_id = self._holders.append(str(sender))

        holder.join(value, node_id)

        self._system_score.setStake(self.getStaked() + value)

        delegation_info: Delegation = {
            "address": PREP_ADDRESS,
            "value": self.getDelegation()["totalDelegated"] + value
        }

        self._system_score.setDelegation([delegation_info])
        self.Join(sender, value)

    def _leave(self, _account: Address, _value: int):
        if _value is None:
            _value = self._balances[self.msg.sender]
        if _value < 0:
            revert("LiquidICX: Leaving value cannot be less than zero.")

        Holder(self.db, _account).requestLeave(_value)

        self._balances[_account] = self._balances[_account] - _value
        self._total_supply.set(self._total_supply.get() - _value)

    def _transfer(self, _from: Address, _to: Address, _value: int, _data: bytes) -> None:
        """
        Send LICX from one wallet to another
        :param _from: Sender's wallet
        :param _to: Recipient's wallet
        :param _value: To be transferred LICX
        :param _data: Optional data for Event
        """

        # Checks the sending value and balance.
        if _value < 0:
            revert("LiquidICX: Transferring value cannot be less than zero.")
        if self._balances[_from] < _value:
            revert("LiquidICX: Out of balance")
        if _to == ZERO_WALLET_ADDRESS:
            revert("LiquidICX: Can not transfer LICX to zero wallet address.")

        sender = Holder(self.db, _from)
        receiver = Holder(self.db, _to)

        self._balances[_from] = self._balances[_from] - _value
        if sender.node_id and self._balances[_from] < self._min_value_to_get_rewards.get() and sender.locked == 0:
            self._holders.remove(sender.node_id)
            sender.node_id = 0

        self._balances[_to] = self._balances[_to] + _value
        if not receiver.node_id and self._balances[_to] >= self._min_value_to_get_rewards.get():
            node_id = self._holders.append(str(_to))
            receiver.node_id = node_id

        if _to.is_contract:
            # If the recipient is SCORE,
            # then calls `tokenFallback` to hand over control.
            recipient_score = self.create_interface_score(_to, TokenFallbackInterface)
            recipient_score.tokenFallback(_from, _value, _data)

        # Emits an event log `Transfer`
        self.Transfer(_from, _to, _value, _data)
        Logger.debug(f'Transfer({_from}, {_to}, {_value}, {_data})', TAG)

    def _burn(self, _account: Address, _amount: int) -> None:
        """
        Burn (destroy) a wallet's LICX
        :param _account: Wallet
        :param _amount: to be burned LICX
        """

        if _account == ZERO_WALLET_ADDRESS:
            revert("LiquidICX: burn from the zero address")
        if self._balances[_account] - _amount < 0:
            revert("LiquidICX: burn amount exceeds balance")

        self._balances[_account] = self._balances[_account] - _amount
        self._total_supply.set(self.totalSupply() - _amount)

        self.Transfer(_account, ZERO_WALLET_ADDRESS, _amount, b'None')

    def _mint(self, _account: Address, _amount: int, _internal: bool = False) -> None:
        """
        Issue new LICX to a wallet
        :param _account: wallet
        :param _amount: Amount of LICX
        :param _internal: Whether the LICX come from rewards or not
        """

        self._balances[_account] = self._balances[_account] + _amount
        self._total_supply.set(self.totalSupply() + _amount)

        if _internal:
            self.Transfer(ZERO_WALLET_ADDRESS, _account, _amount, b'None')

