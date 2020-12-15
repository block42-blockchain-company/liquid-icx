import os
import pprint as pp
import fileinput

from iconsdk.signed_transaction import SignedTransaction
from tbears.libs.icon_integrate_test import SCORE_INSTALL_ADDRESS

from score.join_score.tests.deploy import deployJoinScore
from score.liquid_icx.tests.test_integrate_base import LICXTestBase


class LiquidICXTest(LICXTestBase):

    LOCAL_NETWORK_TEST = True

    def setUp(self, **kwargs):
        super().setUp()
        self._score_address = self._deploy_score()["scoreAddress"]
        print(f"New SCORE address: {self._score_address}")

    def test_score_update(self):
        # update SCORE
        tx_result = self._deploy_score(self._score_address)
        self.assertEqual(self._score_address, tx_result['scoreAddress'], msg=pp.pformat(tx_result))

    def test_0_join_delegate_stake_fallback(self):
        """
        1. Join as owner and then join with another 10 random generated wallets and check the length of the linkedlist
        2. Perform detailed owner's wallet check
        3. Check staked, delegate values
        4. Try to send ICX directly to contract ( fallback function )
        """
        # 1
        self.assertEqual(self._get_wallets(), [])
        join_tx = self._join()
        self.assertEqual(len(self._get_wallets()), 1, msg=pp.pformat(join_tx))
        self._n_join(10)
        self.assertEqual(len(self._get_wallets()), 11)
        join_tx = self._join()
        self.assertEqual(len(self._get_wallets()), 11, msg=pp.pformat(join_tx))
        # 2
        owner = self._get_wallet()
        self.assertEqual(owner["locked"], hex(2 * 10 * 10**18), msg=pp.pformat(owner))
        self.assertEqual(len(owner["join_values"]), 2, msg=pp.pformat(owner))
        self.assertEqual(len(owner["unlock_heights"]), 2, msg=pp.pformat(owner))
        self.assertEqual(len(owner["join_values"]), 2, msg=pp.pformat(owner))
        # 3
        self.assertEqual(self._get_staked(), hex(12 * 10 * 10**18), msg=pp.pformat(owner))
        self.assertEqual(self._get_delegation()["totalDelegated"], hex(12 * 10 * 10**18), msg=pp.pformat(owner))
        # 4
        fallback_tx = self._transfer_icx_from_to(self._wallet, self._score_address, value=5, condition=False)
        self.assertIn("LICX does not accept ICX", fallback_tx["failure"]["message"])

    def test_1_join_balance_transfer_leave(self):
        """
        1. Join as owner with 12 ICX and perform basic checks
        2. Try to transfer LICX, should fail
        3. Try to leave with value, that is less than allowed ( should fail )
        4. Try to leave with LICX, that you don't have yet ( should fail )
        5. Check if wallet's values are really untouched
        """
        # 1
        self._join(value=12)
        self.assertEqual(len(self._get_wallets()), 1)
        self.assertEqual(self._balance_of(), hex(0), msg=self._balance_of())
        self.assertEqual(self._total_supply(), hex(0), msg=self._total_supply())
        # 2
        transfer_tx = self._transfer_licx_from_to(self._wallet, to=self._wallet2.get_address())
        self.assertEqual(transfer_tx["status"], 0, msg=pp.pformat(transfer_tx))
        self.assertEqual(transfer_tx["failure"]["message"], "LiquidICX: Out of balance.")
        self.assertEqual(self._balance_of(), hex(0), msg=self._balance_of())
        # 3
        leave_tx = self._leave(value=5, condition=False)
        self.assertEqual(leave_tx["status"], 0, msg=pp.pformat(leave_tx))
        self.assertIn("Leaving value cannot be less than", leave_tx["failure"]["message"], msg=pp.pformat(leave_tx))
        # 4
        leave_tx = self._leave(value=11, condition=False)
        self.assertEqual(leave_tx["status"], 0, msg=pp.pformat(leave_tx))
        self.assertEqual(leave_tx["failure"]["message"], "LiquidICX: Out of balance.", msg=pp.pformat(leave_tx))
        # 5
        owner = self._get_wallet()
        self.assertEqual(owner["locked"], hex(12 * 10**18), msg=pp.pformat(owner))
        self.assertEqual(owner["unstaking"], hex(0), msg=pp.pformat(owner))

    def test_2_join_cap(self):
        """
        1. Set a cap of 100 ICX
        2. Join as long as cap is not reached
        3. Increase cap and again join as long the cap is not reached
        4. Check length of linked list, and owner's wallet detailed values
        """
        # 1
        self._set_cap(100)
        self.assertEqual(self._get_cap(), hex(100 * 10 ** 18))
        # 2
        while True:
            join_tx = self._join(value=30)
            if not join_tx["status"]:
                self.assertIn("Currently impossible to join the pool", join_tx["failure"]["message"], msg=pp.pformat(join_tx))
                break
        # 3
        self._set_cap(200)
        self.assertEqual(self._get_cap(), hex(200 * 10 ** 18))
        while True:
            join_tx = self._join(value=30)
            if not join_tx["status"]:
                self.assertIn("Currently impossible to join the pool", join_tx["failure"]["message"], msg=pp.pformat(join_tx))
                break
        # 4
        self.assertEqual(1, len(self._get_wallets()))
        owner = self._get_wallet(self._wallet.get_address())
        self.assertEqual(6, len(owner["join_values"]))
        self.assertEqual(hex(6 * 30 * 10 ** 18), owner["locked"])

    def test_3_join_with_SCORE(self):
        """
        1. Deploy SCORE, that will join to LICX protocol
        2. SET LICX address for the joining score
        3. Join with that SCORE, and check if it appears in linked_list
        4. Join with hx wallet and check wallets length
        """
        # 1
        deploy_tx = deployJoinScore(self._wallet, self._icon_service, self.process_transaction)
        self.assertEqual(True, deploy_tx["status"], msg=pp.pformat(deploy_tx))
        test_join_score_address = deploy_tx["scoreAddress"]
        print(f"Joining SCORE ddress: {test_join_score_address}")
        paras = {"address": self._score_address}
        # 2
        tx = self._build_transaction(to=test_join_score_address, method="setLICXAddress", params=paras)
        tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
        self.assertEqual(tx_result["status"], True, msg=pp.pformat(tx_result))
        # 3
        tx = self._build_transaction(to=test_join_score_address, value=10 * 10**18, method="joinLICX")
        tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
        self.assertEqual(tx_result["status"], True, msg=pp.pformat(tx_result))
        self.assertTrue(test_join_score_address in self._get_wallets())
        # 4
        self._join()
        self.assertEqual(len(self._get_wallets()), 2, msg=pp.pformat(self._get_wallets()))

    def test_4_join_with_custom_preps(self):
        """
        1. Join with 20 ICX, vote for two different preps with 10 ICX each and perform basic checks
        2. Second join with additional 10 ICX, which are delegated to first prep in list
        :return:
        """
        # 1
        prep_list = ["hxc60380ef4c1e76595a30fa40d7b519fb3c832db0",
                     "hx487a43ade1479b6e7aa3d6f898a721b8ba9a4ccc",
                     "hxec79e9c1c882632688f8c8f9a07832bcabe8be8f"]
        delegation = {
            prep_list[0]: 6 * 10**18,
            prep_list[1]: 6 * 10**18,
            prep_list[2]: 6 * 10**18
        }
        join_tx = self._join(value=18, prep_list=delegation)
        self.assertTrue(join_tx["status"], msg=pp.pformat(join_tx))
        self.assertEqual(len(self._get_wallets()), 1)
        # check wallet
        owner = self._get_wallet()
        pp.pprint(owner)
        self.assertEqual(int(owner["delegation_values"][0], 16), 6*10**18, msg=pp.pformat(owner))
        self.assertEqual(int(owner["delegation_values"][1], 16), 6*10**18, msg=pp.pformat(owner))
        self.assertEqual(int(owner["delegation_values"][2], 16), 6*10**18, msg=pp.pformat(owner))
        self.assertEqual(owner["delegation_addr"][0], prep_list[0], msg=pp.pformat(owner))
        self.assertEqual(owner["delegation_addr"][1], prep_list[1], msg=pp.pformat(owner))
        self.assertEqual(owner["delegation_addr"][2], prep_list[2], msg=pp.pformat(owner))
        # check contract staking/delegating
        self.assertEqual(self._get_staked(), hex(18 * 10 ** 18), msg=pp.pformat(owner))
        self.assertEqual(self._get_delegation()["totalDelegated"], hex(18 * 10 ** 18), msg=pp.pformat(owner))
        delegations = self._get_delegation()["delegations"]
        self.assertEqual(delegations[0]["value"], hex(6 * 10 ** 18), msg=pp.pformat(owner))
        self.assertEqual(delegations[0]["address"], prep_list[0], msg=pp.pformat(owner))
        self.assertEqual(delegations[1]["value"], hex(6 * 10 ** 18), msg=pp.pformat(owner))
        self.assertEqual(delegations[1]["address"], prep_list[1], msg=pp.pformat(owner))
        self.assertEqual(delegations[2]["value"], hex(6 * 10 ** 18), msg=pp.pformat(owner))
        self.assertEqual(delegations[2]["address"], prep_list[2], msg=pp.pformat(owner))
        # 2
        delegation = {prep_list[0]: 10 * 10 ** 18}
        join_tx = self._join(value=10, prep_list=delegation)
        self.assertTrue(join_tx["status"], msg=pp.pformat(join_tx))
        # check contract staking/delegating
        self.assertEqual(self._get_staked(), hex(28 * 10 ** 18), msg=pp.pformat(owner))
        self.assertEqual(self._get_delegation()["totalDelegated"], hex(28 * 10 ** 18), msg=pp.pformat(owner))
        delegations = self._get_delegation()["delegations"]
        self.assertEqual(delegations[0]["value"], hex(16 * 10 ** 18), msg=pp.pformat(owner))
        self.assertEqual(delegations[0]["address"], prep_list[0], msg=pp.pformat(owner))
        self.assertEqual(delegations[1]["value"], hex(6 * 10 ** 18), msg=pp.pformat(owner))
        self.assertEqual(delegations[1]["address"], prep_list[1], msg=pp.pformat(owner))
        self.assertEqual(delegations[2]["value"], hex(6 * 10 ** 18), msg=pp.pformat(owner))
        self.assertEqual(delegations[2]["address"], prep_list[2], msg=pp.pformat(owner))



        # TODO
        # 1. Write test-case, where user does not vote at first, and then votes at next join







