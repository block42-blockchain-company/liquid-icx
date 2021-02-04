import iconservice
from .scorelib.consts import *
from .wallet import Wallet
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

    @eventlog(indexed=2)
    def LeaveRequest(self, _from: Address, _value: int):
        pass

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        pass

    @eventlog(indexed=0)
    def Distribute(self, _block_height: int):
        pass

    @eventlog(indexed=0)
    def Claim(self):
        pass

    @eventlog(indexed=0)
    def Vote(self, _from: Address):
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
        self._wallets = LinkedListDB("wallets", db, str)

        self._min_value_to_get_rewards = VarDB("min_value_to_get_rewards", db, int)

        self._rewards = VarDB("rewards", db, int)
        self._new_unlocked_total = VarDB("new_unlocked_total", db, int)
        self._total_unstake_in_term = VarDB("total_unstake_in_term", db, int)

        self._last_distributed_height = VarDB("last_distributed_height", db, int)

        self._current_distribute_linked_list_id = VarDB("current_distribute_linked_list_id", db, int)
        self._iteration_limit = VarDB("iteration_limit", db, int)

        self._distributing = VarDB("distributing", db, bool)

        self._cap = VarDB("cap", db, int)

        self._delegation = DictDB("delegation", db, int)
        self._delegation_keys = ArrayDB("delegation_keys", db, Address)

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

        self._min_value_to_get_rewards.set(10 * 10 ** _decimals)
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
        return self._balances[_owner] - Wallet(self.db, _owner).unstaking

    @external(readonly=True)
    def lockedOf(self, _owner: Address) -> int:
        return Wallet(self.db, _owner).locked

    @external(readonly=True)
    def getWallet(self, _address: Address) -> dict:
        return Wallet(self.db, _address).serialize()

    @external(readonly=True)
    def getWallets(self) -> list:
        result = []
        for item in self._wallets:
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
    def getMinValueToGetRewards(self) -> int:
        return self._min_value_to_get_rewards.get()

    @external(readonly=True)
    def getTotalUnstakeInTerm(self) -> int:
        return self._total_unstake_in_term.get()

    @external(readonly=True)
    def getWalletByNodeID(self, node_id: int) -> Address:
        return self._wallets.node_value(node_id)

    @external(readonly=True)
    def getCap(self) -> int:
        return self._cap.get()

    @external(readonly=True)
    def newUnlockedTotal(self) -> int:
        return self._new_unlocked_total.get()

    @external
    def transfer(self, _to: Address, _value: int, _data: bytes = None) -> None:
        """
        External entry function to send LICX from one wallet to another
        :param _to: Recipient's wallet
        :param _value: LICX amount to transfer
        :param _data: Optional information for transfer Event
        """

        if self._distributing.get():
            revert("LiquidICX: Can not transfer while distribute cycle.")
        if _value < 0:
            revert("LiquidICX: Transferring value cannot be less than zero.")
        if _to == ZERO_WALLET_ADDRESS:
            revert("LiquidICX: Can not transfer LICX to zero wallet address.")

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

    @external
    def setMinValueToGetRewards(self, _value: int) -> None:
        """
        Change to minimum amount of LICX needed to hold in a wallet to receive rewards
        :param _value: min LICX amount
        """

        if self.msg.sender != self.owner:
            revert("LiquidICX: Only owner function at current state.")
        if _value <= 0:
            revert("LiquidICX: 'iteration limit' has to be > 0.")

        self._min_value_to_get_rewards.set(_value)

    @external
    def setCap(self, _value: int):
        """
        Change the maximum amount of ICX that can get pooled in the SCORE
        :param _value: max ICX amount
        """

        if self.msg.sender != self.owner:
            revert("LiquidICX: Only owner function at current state.")
        self._cap.set(_value * 10 ** self._decimals.get())

    @payable
    @external
    def join(self, delegation: str = None):
        """
        External entry point to join the LICX pool
        :param delegation: list of preps a user wants to vote for in string JSON format
        """

        if self.msg.value < self._min_value_to_get_rewards.get():
            revert("LiquidICX: Joining value cannot be less than the minimum join value")

        if self._cap.get() <= self.getStaked() + self.msg.value:
            revert("LiquidICX: Currently impossible to join the pool")

        self._join(self.msg.sender, self.msg.value, json_loads(delegation))

    @external
    def leave(self, _value: int = None):
        """
        External entry point to leave the LICX pool
        :param _value: amount of LICX to convert back to ICX
        """

        if _value is None:
            _value = self._balances[self.msg.sender]

        self._leave(self.msg.sender, _value)

    @external
    def claim(self):
        """
        External entry point to claim ICX
        """

        wallet = Wallet(self.db, self.msg.sender)
        claim_amount = wallet.claim()

        if claim_amount:
            if self.icx.send(self.msg.sender, claim_amount):
                self.Claim()
            else:
                revert("LiquidICX: Could not send ICX to the given address.")

    @external
    def vote(self, _delegation: str):
        """
        External entry point to change a wallet's current delegation
        :param delegation: list of preps a user wants to vote for in string JSON format
        """
        delegation = json_loads(_delegation)
        if delegation is None:
            revert("LIquidICX: Delegation can not be None")

        self._vote(self.msg.sender, delegation)

    @external
    def distribute(self):
        """
        External entry point to execute the distribute process
        """

        if not len(self._wallets):
            revert("LiquidICX: No wallets joined yet.")
        if self._last_distributed_height.get() >= self._system_score.getPRepTerm()["startBlockHeight"]:
            revert("LiquidICX: Distribute was already called this term.")

        self._distribute()

    @payable
    def fallback(self):
        """
        Called when anyone sends ICX to the SCORE without specifying a method.
        """

        revert('LiquidICX: LICX does not accept ICX. If you want to enter the pool, you need to call "join" method.')

    # ================================================
    #  Internal methods
    # ================================================

    def _join(self, _sender: Address, _amount: int, _delegation: dict) -> None:
        """
        Add a wallet to the LICX pool and issue LICX to it.
        If user passes delegation to entry point function, it will delegate to this specific preps,
        otherwise it will distribute the voting power within the preps that SCORE is delegating.
        :param sender: Wallet that wants to join
        :param amount: Amount of ICX to join the pool
        :param delegation: preps, that user wants delegate to ( key -> prep_address, value -> delegation amount)
        """

        # Create wallet object and append to linked list if first time joining
        wallet = Wallet(self.db, _sender)
        if not wallet.exists():
            wallet.node_id = self._wallets.append(str(_sender))

        if _delegation is None:
            self._getDelegationDictProportionalToSCORE(_amount)

        wallet.join(_amount, _delegation, self)
        self._system_score.setStake(self.getStaked() + _amount)
        self._delegate()
        self.Join(_sender, _amount)

    def _leave(self, sender: Address, _value: int):
        """
        Internal method, which adds a leave request to a specific address.
        Requests are then later resolved in distribute cycle, once per term.
        :param sender: Address, which is requesting leave.
        :param _value: Amount of LICX for a leave request
        """

        if _value < self._min_value_to_get_rewards.get():
            revert(f"LiquidICX: Leaving value cannot be less than {self._min_value_to_get_rewards.get()}.")
        if self._balances[sender] < _value:
            revert("LiquidICX: Out of balance.")

        wallet = Wallet(self.db, sender)
        wallet.requestLeave(_value)

        self.LeaveRequest(sender, _value)

    def _vote(self, _sender: Address, _delegations: dict):
        """
        Internal method, which allows user to change delegation.
        It removes all previous delegations from wallet object and adds the new delegation, that user passed
        to the external vote function.
        If the sum of previous delegation does not match with the sum of new delegation, the transaction gets reverted.
        :param sender: sender's address
        :param delegation: new delegations dictionary
        """

        wallet = Wallet(self.db, _sender)
        if not wallet.hasVotingPower():
            revert("LiquidICX: You do not have any voting power.")

        sum_undelegated = self._removeDelegations(wallet)
        sum_delegated = self._addAbsoluteDelegations(wallet, _delegations)

        if sum_undelegated != sum_delegated:
            revert("LiquidICX: New total delegation should match with the previous total delegation.")

        self._delegate()
        self.Vote(_sender)

    def _transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        """
        Send LICX from one wallet to another
        :param _from: Sender's wallet
        :param _to: Recipient's wallet
        :param _value: To be transferred LICX
        :param _data: Optional data for Event
        """

        sender = Wallet(self.db, _from)
        receiver = Wallet(self.db, _to)

        # Checks the sending value and balance.
        if self._balances[_from] - sender.unstaking < _value:
            revert("LiquidICX: Out of balance.")

        sender.subtractDelegationsProportionallyToWallet(self, _value)

        self._balances[_from] = self._balances[_from] - _value
        self._check_wallet_has_enough_funds(sender)

        # receiver has already voting power, add to existing one, otherwise proportionally divide between all
        # delegated preps
        if receiver.hasVotingPower():
            self._addDelegationsProportionallyToWallet(receiver,_value)
        else:
            self._addDelegationsProportionallyToSCORE(receiver, _value)

        self._balances[_to] = self._balances[_to] + _value
        if not receiver.exists() and self._balances[_to] >= self._min_value_to_get_rewards.get():
            node_id = self._wallets.append(str(_to))
            receiver.node_id = node_id

        if _to.is_contract:
            recipient_score = self.create_interface_score(_to, TokenFallbackInterface)
            recipient_score.tokenFallback(_from, _value, _data)

        self._delegate(stake=False)
        self.Transfer(_from, _to, _value, _data)

    def _distribute(self):
        """
        Distribute I-Score rewards once per term.
        Iterate over all wallets >= self._min_value_to_get_rewards and give them their reward share.

        When the last wallet in the linked list is being processed, the summed up values are being used to redelegate and to
        update the total_supply of LICX. After that all the variables used are being reset (set to default state).
        This function has to be called multiple times until we iterated over all wallets >= self._min_value_to_get_rewards.
        """

        self._distributionSetup()

        current_linked_list_id = self._current_distribute_linked_list_id.get()
        i = 0
        # current_linked_list_id becomes negative when we reached the end of the linked list
        while i < self._iteration_limit.get() and current_linked_list_id >= 0:
            self._distributeOneWallet(current_linked_list_id)
            current_linked_list_id = self._getNextLinkedListId(current_linked_list_id)
            i += 1

        if current_linked_list_id >= 0:
            self._current_distribute_linked_list_id.set(current_linked_list_id)
        else:
            self._redelegate()
            self._endDistribution()

    # ================================================
    #  Helper methods
    # ================================================

    def _claimRewards(self):
        """
        Claim IScore rewards. It is called only once per term, at the start of the cycle.
        """
        self._rewards.set(0)
        self._rewards.set(self._system_score.queryIScore(self.address)["estimatedICX"])
        self._system_score.claimIScore()
        self._distributing.set(True)

    def _redelegate(self):
        """
        Re-stake and re-delegate with the rewards claimed at the start of the cycle.
        """
        restake_value = self.getStaked() + self._rewards.get() - self._total_unstake_in_term.get()
        if restake_value >= self.getStaked():
            self._system_score.setStake(restake_value)
            self._delegate()
        else:
            self._delegate()
            self._system_score.setStake(restake_value)

    def _endDistribution(self):
        """
        The function sets the following VarDB to the default state and updates the total supply of LICX.
        """

        self._total_supply.set(self.totalSupply() + self._rewards.get() + self._new_unlocked_total.get() -
                               self._total_unstake_in_term.get())
        self._rewards.set(0)
        self._new_unlocked_total.set(0)
        self._total_unstake_in_term.set(0)
        self._current_distribute_linked_list_id.set(0)
        self._last_distributed_height.set(self._system_score.getPRepTerm()["startBlockHeight"])
        self._distributing.set(False)
        self.Distribute(self.block_height)

    def _delegate(self, stake=True):
        """
        Iterates through internal delegation dictionary and builds up delegation list .
        :param stake: If true the function also stakes new value, which is the sum of all delegations.
        """

        delegations = []
        stake_sum = 0

        for address in self._delegation_keys:
            delegations.append({
                "address": address,
                "value": self._delegation[address]
            })
            stake_sum += self._delegation[address]

        if stake:
            self._system_score.setStake(stake_sum)
        self._system_score.setDelegation(delegations)

    def _calculateWalletRewards(self, _wallet: Wallet, _address: Address) -> int:
        wallet_balance = self._balances[_address]

        if wallet_balance >= self._min_value_to_get_rewards.get() and self._total_supply.get():

            wallet_rewards = int(wallet_balance / self._total_supply.get() * self._rewards.get())
            _wallet.calcDistributeDelegations(wallet_rewards, wallet_balance, self._delegation)

            return wallet_rewards
        else:
            return 0

    def _distributionSetup(self):
        if not self._rewards.get():
            self._claimRewards()
            self._current_distribute_linked_list_id.set(self._wallets.get_head_node().id)  # get head id for start iteration

    def _distributeOneWallet(self, _linked_list_id) -> None:
        """
        Perform the distribution steps for the wallet with the ID of _linked_list_id.
        First reward calculation is done.
        Then join and leave queues are being resolved.
        Rewards, unlocked and leave values are then being used to update wallet's balance and are added to:
            * new_unlocked_total
            * total_unstake_in_term
        """

        address = Address.from_string(self._wallets.node_value(_linked_list_id))
        wallet = Wallet(self.db, address)

        wallet_reward_licx = self._calculateWalletRewards(wallet, address)
        wallet_unlocked_licx = wallet.unlock()
        wallet_leave_licx = wallet.leave(self)

        self._balances[address] = self._balances[address] + \
                                       wallet_unlocked_licx + \
                                       wallet_reward_licx - \
                                       wallet_leave_licx

        self._new_unlocked_total.set(self._new_unlocked_total.get() + wallet_unlocked_licx)
        self._total_unstake_in_term.set(self._total_unstake_in_term.get() + wallet_leave_licx)

    def _getNextLinkedListId(self, _linked_list_id: int) -> int:
        """
        Return the next ID of the wallet linked list, or return -1 if there's no following element.
        """

        address = Address.from_string(self._wallets.node_value(_linked_list_id))
        wallet = Wallet(self.db, address)

        try:
            # delete from wallets linked list
            if not len(wallet.join_values) \
                    and self._balances[address] < self._min_value_to_get_rewards.get():
                next_id = self._wallets.next(_linked_list_id)
                self._wallets.remove(wallet.node_id)
            else:
                next_id = self._wallets.next(_linked_list_id)
        except StopIteration:
            return -1
        return next_id

    def _removeDelegations(self, _wallet: Wallet) -> int:
        """
        Remove all delegations from a wallet
        Return the sum of all removed delegations
        """

        sum_undelegated = 0
        while len(_wallet.delegation_address) != 0:
            prep_address = _wallet.delegation_address.pop()
            deleg = _wallet.delegation_value.pop()
            self._delegation[prep_address] -= deleg
            sum_undelegated += deleg
            if self._delegation[prep_address] <= 0:
                Utils.remove_from_array(self._delegation_keys, prep_address)

        return sum_undelegated

    def _addAbsoluteDelegations(self, _wallet: Wallet, _delegations: dict):
        """
        Add delegations to a wallet
        Return the sum all added delegations
        """

        sum_delegated = 0
        for address, value in _delegations.items():
            prep_address: Address = Address.from_string(address)

            if prep_address in self._delegation:
                self._delegation[prep_address] += value
            elif not Utils.isPrep(self.db, prep_address):
                revert("LiquidICX: Given address is not a P-Rep.")
            else:
                self._delegation[prep_address] = value
                self._delegation_keys.put(prep_address)

            _wallet.delegation_value.put(value)
            _wallet.delegation_address.put(prep_address)
            sum_delegated += value

        return sum_delegated

    def _addDelegationsProportionallyToWallet(self, _wallet: Wallet, _value: int):
        for i in range(len(_wallet.delegation_value)):
            basis_point = Utils.calcBPS(_wallet.delegation_value[i], self._balances[_wallet.address])
            additional_delegation = int((_value * basis_point) / 10000)

            _wallet.delegation_value[i] += additional_delegation
            self._delegation[_wallet.delegation_address[i]] += additional_delegation

    def _addDelegationsProportionallyToSCORE(self, _wallet: Wallet, _value: int):
        delegations = self._getDelegationDictProportionalToSCORE(_value)

        for address, value in delegations.items():
            prep_address: Address = Address.from_string(address)
            _wallet.delegation_value.put(value)
            _wallet.delegation_address.put(prep_address)
            self._delegation[prep_address] += value

    def _getDelegationDictProportionalToSCORE(self, _total_voting_amount: int) -> dict:
        """
        Return a dict that has the SCORE delegations downscaled to an amount
        :param _total_voting_amount: amount to downscale the SCORE delegations to
        """

        proportional_delegations = {}
        if len(self._delegation_keys) != 0:
            for i in self._delegation_keys:
                basis_point = Utils.calcBPS(self._delegation[i], self._total_supply.get())
                delegation_value = int((_total_voting_amount * basis_point) / 10000)
                proportional_delegations[str(self._delegation_keys[i])] = delegation_value
        else:
            proportional_delegations[str(PREP_ADDRESS)] = _total_voting_amount

        return proportional_delegations

    def _check_wallet_has_enough_funds(self, _wallet: Wallet):
        if _wallet.exists() and self._balances[_wallet.address] < self._min_value_to_get_rewards.get() \
                and _wallet.locked == 0:
            self._wallets.remove(_wallet.node_id)
            _wallet.node_id = 0
