import os
import pprint as pp
import fileinput
import time
from asyncio import sleep

from iconsdk.signed_transaction import SignedTransaction
from iconservice.icon_constant import GOVERNANCE_ADDRESS
from tbears.libs.icon_integrate_test import SCORE_INSTALL_ADDRESS

from score.join_score.tests.deploy import deployJoinScore
from score.liquid_icx.tests.test_integrate_base import LICXTestBase


class LiquidICXTest(LICXTestBase):
    LOCAL_NETWORK_TEST = True
    TERM_LENGTH = 43120

    def setUp(self, **kwargs):
        super().setUp()
        self._score_address = self._deploy_score()["scoreAddress"]
        print(f"New SCORE address: {self._score_address}")
        if self.LOCAL_NETWORK_TEST:
            self.TERM_LENGTH = 30
            self.replace_in_consts_py("TERM_LENGTH", "43120", "30")

    def tearDown(self):
        super().tearDown()
        if self.LOCAL_NETWORK_TEST:
            self.TERM_LENGTH = 43120
            self.replace_in_consts_py("TERM_LENGTH", "30", "43120")

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
        self.assertEqual(owner["locked"], hex(2 * 10 * 10 ** 18), msg=pp.pformat(owner))
        self.assertEqual(len(owner["join_values"]), 2, msg=pp.pformat(owner))
        self.assertEqual(len(owner["unlock_heights"]), 2, msg=pp.pformat(owner))
        # 3
        self.assertEqual(self._get_staked(), hex(12 * 10 * 10 ** 18), msg=pp.pformat(owner))
        self.assertEqual(self._get_delegation()["totalDelegated"], hex(12 * 10 * 10 ** 18), msg=pp.pformat(owner))
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
        self.assertEqual(owner["locked"], hex(12 * 10 ** 18), msg=pp.pformat(owner))
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
                self.assertIn("Currently impossible to join the pool", join_tx["failure"]["message"],
                              msg=pp.pformat(join_tx))
                break
        # 3
        self._set_cap(200)
        self.assertEqual(self._get_cap(), hex(200 * 10 ** 18))
        while True:
            join_tx = self._join(value=30)
            if not join_tx["status"]:
                self.assertIn("Currently impossible to join the pool", join_tx["failure"]["message"],
                              msg=pp.pformat(join_tx))
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
        tx = self._build_transaction(to=test_join_score_address, value=10 * 10 ** 18, method="joinLICX")
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
        delegation = {
            # self.prep_list[0]: 6 * 10**18,
            self.prep_list[1]: 6 * 10 ** 18,
            self.prep_list[2]: 6 * 10 ** 18
        }
        join_tx = self._join(value=12, prep_list=delegation)
        pp.pprint(join_tx)
        self.assertTrue(join_tx["status"], msg=pp.pformat(join_tx))
        self.assertEqual(len(self._get_wallets()), 1)
        # check wallet
        # owner = self._get_wallet()
        # self.assertEqual(6*10**12, int(owner["delegation_values"][0], 16), msg=pp.pformat(owner))
        # self.assertEqual(6*10**12, int(owner["delegation_values"][1], 16), msg=pp.pformat(owner))
        # self.assertEqual(6*10**12, int(owner["delegation_values"][2], 16), msg=pp.pformat(owner))
        # self.assertEqual(self.prep_list[0], owner["delegation_addr"][0], msg=pp.pformat(owner))
        # self.assertEqual(self.prep_list[1], owner["delegation_addr"][1] , msg=pp.pformat(owner))
        # self.assertEqual(self.prep_list[2], owner["delegation_addr"][2], msg=pp.pformat(owner))
        # # check contract staking/delegating
        # self.assertEqual(hex(12 * 10 ** 12), self._get_staked(), msg=pp.pformat(owner))
        # self.assertEqual(hex(12 * 10 ** 12), self._get_delegation()["totalDelegated"], msg=pp.pformat(owner))
        # delegations = self._get_delegation()["delegations"]
        # self.assertEqual(hex(6 * 10 ** 12), delegations[0]["value"], msg=pp.pformat(owner))
        # self.assertEqual(self.prep_list[0], delegations[0]["address"], msg=pp.pformat(owner))
        # self.assertEqual(hex(6 * 10 ** 12), delegations[1]["value"], msg=pp.pformat(owner))
        # self.assertEqual(self.prep_list[1], delegations[1]["address"], msg=pp.pformat(owner))
        # self.assertEqual(hex(6 * 10 ** 12), delegations[2]["value"], msg=pp.pformat(owner))
        # self.assertEqual(self.prep_list[2], delegations[2]["address"], msg=pp.pformat(owner))
        # 2
        delegation = {self.prep_list[0]: 10 * 10 ** 18}
        join_tx = self._join(value=10, prep_list=delegation)
        pp.pprint(join_tx)
        self.assertTrue(join_tx["status"], msg=pp.pformat(join_tx))
        # check contract staking/delegating
        # self.assertEqual(self._get_staked(), hex(28 * 10 ** 18), msg=pp.pformat(owner))
        # self.assertEqual(self._get_delegation()["totalDelegated"], hex(28 * 10 ** 18), msg=pp.pformat(owner))
        # delegations = self._get_delegation()["delegations"]
        # self.assertEqual(delegations[0]["value"], hex(16 * 10 ** 18), msg=pp.pformat(owner))
        # self.assertEqual(delegations[0]["address"], self.prep_list[0], msg=pp.pformat(owner))
        # self.assertEqual(delegations[1]["value"], hex(6 * 10 ** 18), msg=pp.pformat(owner))
        # self.assertEqual(delegations[1]["address"], self.prep_list[1], msg=pp.pformat(owner))
        # self.assertEqual(delegations[2]["value"], hex(6 * 10 ** 18), msg=pp.pformat(owner))
        # self.assertEqual(delegations[2]["address"], self.prep_list[2], msg=pp.pformat(owner))
        #

    def test_5(self):
        """
        0. Wait till next term starts
        1a. Delegate to a prep, which should fail, because the joining and total delegation amount don't match
        1b. Delegate with same paramaters, but correct joining amount
        2. Transfer ICX to a second wallet and delegate 10 ICX to the same prep as first wallet
        3. Prepare delegation dictionary and delegate to the 2 new preps
        4. Perform checks
        5. Wait till the unlock heights to unlock the LICX. Distribute and perform checks
        """
        # 0
        next_term = self._getNextTermStart()
        while self._icon_service.get_block("latest")["height"] < next_term:
            time.sleep(1)
        print("-----Starting test-case------")
        # 1a
        delegation_value = 10 * 10 ** 18
        delegation = {
            self.prep_list[0]: delegation_value,
        }
        join_tx = self._join(value=18, prep_list=delegation)
        self.assertFalse(join_tx["status"], msg=pp.pformat(join_tx))
        self.assertIn("Delegations values do not match", join_tx["failure"]["message"], msg=pp.pformat(join_tx))
        # 1b
        join_tx = self._join(value=10, prep_list=delegation)
        self.assertTrue(join_tx["status"], msg=pp.pformat(join_tx))
        # 2
        transfer_tx = self._transfer_icx_from_to(self._wallet, self._wallet2, 100)
        self.assertTrue(join_tx["status"], msg=pp.pformat(transfer_tx))
        delegation = {self.prep_list[0]: delegation_value}
        join_tx = self._join(self._wallet2, value=10, prep_list=delegation)
        self.assertTrue(join_tx["status"], msg=pp.pformat(join_tx))
        # 3
        delegation = {
            self.prep_list[1]: delegation_value * 5,
            self.prep_list[2]: delegation_value * 3
        }
        join_tx = self._join(self._wallet2, value=80, prep_list=delegation)
        self.assertTrue(join_tx["status"], msg=pp.pformat(join_tx))
        # 4
        self.assertEqual(self._get_staked(), hex(delegation_value * 10), msg=pp.pformat(self._get_staked()))
        delegations = self._get_delegation()["delegations"]
        self.assertEqual(int(delegations[0]["value"], 16), delegation_value * 2, msg=pp.pformat(delegations))
        self.assertEqual(delegations[0]["address"], self.prep_list[0], msg=pp.pformat(delegations))
        self.assertEqual(int(delegations[1]["value"], 16), delegation_value * 5, msg=pp.pformat(delegations))
        self.assertEqual(delegations[1]["address"], self.prep_list[1], msg=pp.pformat(delegations))
        self.assertEqual(int(delegations[2]["value"], 16), delegation_value * 3, msg=pp.pformat(delegations))
        self.assertEqual(delegations[2]["address"], self.prep_list[2], msg=pp.pformat(delegations))
        # 5
        owner = self._get_wallet()
        print(int(owner["unlock_heights"][-1], 16))
        pp.pprint(f"Term_start: {self._getTermStart()}, Next term start {self._getNextTermStart()}")
        while self._icon_service.get_block("latest")["height"] <= int(owner["unlock_heights"][-1], 16):
            time.sleep(1)
        reward_icx = int(self._queryIScore()["estimatedICX"], 16)
        pp.pprint(reward_icx)
        tx_distribute = self._distribute()
        self.assertEqual(tx_distribute["status"], 1, msg=pp.pformat(tx_distribute))
        owner = self._get_wallet()
        self.assertEqual(owner["locked"], hex(0), msg=pp.pformat(owner))
        self.assertEqual(len(owner["join_values"]), 0, msg=pp.pformat(owner))
        self.assertEqual(len(owner["unlock_heights"]), 0, msg=pp.pformat(owner))
        delegations = self._get_delegation()["delegations"]
        pp.pprint(delegations)
        self.assertEqual(int((delegation_value * 2) + reward_icx * 0.2), int(delegations[0]["value"], 16),
                         msg=pp.pformat(delegations))
        self.assertEqual(delegations[0]["address"], self.prep_list[0], msg=pp.pformat(delegations))
        self.assertEqual(int((delegation_value * 5) + reward_icx * 0.5), int(delegations[1]["value"], 16),
                         msg=pp.pformat(delegations))
        self.assertEqual(delegations[1]["address"], self.prep_list[1], msg=pp.pformat(delegations))
        self.assertEqual(int((delegation_value * 3) + reward_icx * 0.3), int(delegations[2]["value"], 16),
                         msg=pp.pformat(delegations))
        self.assertEqual(delegations[2]["address"], self.prep_list[2], msg=pp.pformat(delegations))

    def test_6(self):
        """
        cx72cf3a2928b11f5c42125f79f68caa02df15eb16

        [{'address': 'hx000e0415037ae871184b2c7154e5924ef2bc075e',
          'value': '0x1158e460913d00000'},
         {'address': 'hx9eec61296a7010c867ce24c20e69588e2832bc52',
          'value': '0x2b5e3af16b1880000'},
         {'address': 'hx2fb8fb849cba40bf59a48ebcef899d6ae45382f4',
          'value': '0x1a055690d9db80000'}]
        """
        # self._score_address = "cx72cf3a2928b11f5c42125f79f68caa02df15eb16"
        # tx_distribute = self._distribute()
        # self.assertEqual(tx_distribute["status"], 1, msg=pp.pformat(tx_distribute))
        # height = self._icon_service.get_block("latest")
        # pp.pprint(height)
        # pp.pprint(self._getTermStart())
        # pp.pprint(self._getNextTermStart())
        # print("-----------")
        # pp.pprint(self._get_delegation())
        # pp.pprint(int(self._get_staked(), 16))
        # pp.pprint(self._queryIScore())

        # join_tx = self._join(value=999)
        # self.assertTrue(join_tx["status"], msg=pp.pformat(join_tx))
        # owner = self._get_wallet()
        # print(("unlocked:", int(owner["unlock_heights"][0], 16)))
        # while (True):
        #     height = self._icon_service.get_block("latest")
        #     pp.pprint(f"Heeight: {height['height']}, Term_start: {self._getTermStart()}, Next term start {self._getNextTermStart()}")
        #     pp.pprint(self._queryIScore())
        #     time.sleep(2)


"""
{'blockHeight': '0x1ca4',
 'estimatedICX': '0x522f76e60c0b',
 'iscore': '0x1410968729f0b29'}
"""
