import fileinput
import os
import time
import unittest

import pprint as pp
from asyncio import Future

from iconsdk.builder.transaction_builder import DeployTransactionBuilder
from iconsdk.exception import JSONRPCException
from iconsdk.icon_service import IconService
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from tbears.libs.icon_integrate_test import SCORE_INSTALL_ADDRESS
from score.liquid_icx.tests.test_integrate_base import LICXTestBase


def _is_distributed(event_logs: list) -> bool:
    for log in event_logs:
        if log["indexed"][0] == 'Distribute(int)':
            return True
    return False


class LiquidICXWithFakeSysSCORETest(LICXTestBase):
    TERM_LENGTH = 43120

    LOCAL_NETWORK_TEST = True

    def setUp(self):
        super().setUp()

        wallet2_balance = self._icon_service.get_balance(self._wallet2.get_address())
        if not wallet2_balance:
            self._transfer_icx_from_to(self._wallet, self._wallet2, 1000)

        self._fake_sys_score = self._deployFakeSystemSCORE()["scoreAddress"]
        print(f"New FAKE SYS SCORE address: {self._fake_sys_score}")

        self.replace_in_consts_py("SYSTEM_SCORE", SCORE_INSTALL_ADDRESS, self._fake_sys_score)
        self._score_address = self._deploy_score()["scoreAddress"]
        print(f"New SCORE address: {self._score_address}")

    def tearDown(self):
        self.replace_in_consts_py("SYSTEM_SCORE", self._fake_sys_score, SCORE_INSTALL_ADDRESS)

    # -----------------------------------------------------------------------
    # ----------------------- testing helper methods ------------------------
    # -----------------------------------------------------------------------
    def _deployFakeSystemSCORE(self):
        dir_path = os.path.abspath(os.path.dirname(__file__))
        score_project = os.path.abspath(os.path.join(dir_path, "../../fake_system_contract"))
        score_content_bytes = gen_deploy_data_content(score_project)

        transaction = DeployTransactionBuilder() \
            .from_(self._wallet.get_address()) \
            .to(SCORE_INSTALL_ADDRESS) \
            .nid(3) \
            .step_limit(10000000000) \
            .nonce(100) \
            .content_type("application/zip") \
            .content(score_content_bytes) \
            .params({}) \
            .build()

        tx_result = self.process_transaction(SignedTransaction(transaction, self._wallet), self._icon_service)
        self.assertTrue(tx_result["status"])
        return tx_result

    def _estimateUnstakeLockPeriod(self) -> dict:
        tx = self._build_transaction(to=self._fake_sys_score, type_="read", method="estimateUnstakeLockPeriod")
        return self.process_call(tx, self._icon_service)

    def _getPRepTerm(self) -> dict:
        tx = self._build_transaction(to=self._fake_sys_score, type_="read", method="getPRepTerm")
        return self.process_call(tx, self._icon_service)

    def _getIISSInfo(self) -> dict:
        tx = self._build_transaction(to=self._fake_sys_score, type_="read", method="getIISSInfo")
        return self.process_call(tx, self._icon_service)

    def _set_block_height(self, _new_height: int):
        paras = {"_new_height": _new_height}
        tx = self._build_transaction(to=self._fake_sys_score, method="setBlockHeight", params=paras)
        tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
        self.assertEqual(self._getIISSInfo()["blockHeight"], hex(_new_height), msg=pp.pformat(tx_result))
        return tx_result

    def _increment_term_for_n(self, n: int = 1):
        current_next_p_rep_term = int(self._getIISSInfo()['nextPRepTerm'], 16)
        current_start_block_height = int(self._getPRepTerm()['startBlockHeight'], 16)

        for i in range(n):
            tx = self._build_transaction(to=self._fake_sys_score,
                                         from_=self._wallet.get_address(),
                                         method="incrementTerm")
            tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
            self.assertTrue(tx_result["status"])

            self.assertEqual(int(self._getIISSInfo()['nextPRepTerm'], 16),
                             current_next_p_rep_term + self.TERM_LENGTH * (i + 1),
                             msg="nextPRepTerm returns wrong value!")
            self.assertEqual(int(self._getPRepTerm()['startBlockHeight'], 16),
                             current_start_block_height + self.TERM_LENGTH * (i + 1),
                             msg="startBlockHeight returns wrong value!")

    def _set_i_score(self, i_score):
        paras = {"_i_score": i_score}
        tx = self._build_transaction(to=self._fake_sys_score, method="setIScore", params=paras)
        tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
        self.assertTrue(tx_result["status"], msg=tx_result)
        return tx_result

    def _query_i_score(self):
        paras = {"address": self._score_address}
        tx = self._build_transaction(to=self._fake_sys_score, type_="read", method="queryIScore", params=paras)
        return self.process_call(tx, self._icon_service)

    # -----------------------------------------------------------------------
    # ------------------------------- tests ---------------------------------
    # -----------------------------------------------------------------------
    def test_0_single_wallet_join_distribute_transfer(self):
        """
        1. User joins with 12 ICX
        2. Tries to transfer, but should fail since LICX is unlocked after 2 terms
        3. Checking if user's data is still untouched / Checking total_supply
        4. Increment term on fake System SCORE
        5. Distribute, so the user has unlocked LICX and perform checks
        6. Check stateDB variables
        7. Transfer 2 LICX to wallet2
        8. Transfer 2 LICX from wallet2 back to owner's wallet
        """
        # 1
        join_value = 12
        tx_join = self._join(value=join_value)
        self.assertTrue(tx_join["status"])
        self.assertEqual(len(self._get_wallets()), 1)
        # 2,3
        tx_transfer = self._transfer_licx_from_to(self._wallet, self._wallet2.get_address())
        self.assertFalse(tx_transfer["status"], msg=pp.pformat(tx_transfer))
        self.assertEqual(tx_transfer["failure"]["message"], "LiquidICX: Out of balance.")
        owner = self._get_wallet()
        self.assertEqual(len(owner["join_values"]), len(owner["unlock_heights"]))
        self.assertEqual(len(owner["join_values"]), 1)
        self.assertEqual(owner["locked"], hex(join_value * 10 ** 18))
        self.assertEqual(self._total_supply(), hex(0))
        # 4
        self._increment_term_for_n(n=2)
        # 5
        tx_distribute = self._distribute()  # user should now have unlocked licx
        self.assertTrue(tx_distribute["status"], msg=pp.pformat(tx_distribute))
        owner = self._get_wallet()
        self.assertEqual(len(owner["join_values"]), len(owner["unlock_heights"]))
        self.assertEqual(len(owner["join_values"]), 0)
        self.assertEqual(owner["locked"], hex(0))
        # 6
        self.assertEqual(self._get_rewards(), hex(0))
        self.assertEqual(self._get_new_unlocked_total(), hex(0))
        self.assertEqual(self._get_total_unstaked_in_term(), hex(0))
        # 6
        tx_transfer = self._transfer_licx_from_to(self._wallet, self._wallet2.get_address(), value=2)
        self.assertTrue(tx_transfer["status"], msg=pp.pformat(tx_transfer))
        self.assertEqual(self._balance_of(self._wallet.get_address()), hex(10 * 10 ** 18))
        self.assertEqual(self._balance_of(self._wallet2.get_address()), hex(2 * 10 ** 18))
        # 7
        tx_transfer = self._transfer_licx_from_to(self._wallet2, self._wallet.get_address(), value=2)
        self.assertTrue(tx_transfer["status"], msg=pp.pformat(tx_transfer))
        self.assertEqual(self._balance_of(self._wallet.get_address()), hex(12 * 10 ** 18))
        self.assertEqual(self._balance_of(self._wallet2.get_address()), hex(0))

    def test_1_single_wallet_join_leave_claim(self):
        """
        1. User joins with 20 ICX
        2. Increment term on fake System SCORE
        3. Distribute, to unlock user's LICX
        4. Make a leave Request, and check value
        5. Increment term and distribute again to resolve leave requests and perform some basic checks
        6. Set new block height on fake System SCORE
        7. Claim back 20 ICX
        """
        # 1
        tx_join = self._join(value=20)
        self.assertTrue(tx_join["status"])
        self.assertEqual(len(self._get_wallets()), 1, msg=pp.pformat(len(self._get_wallets())))
        # 2
        self._increment_term_for_n(n=2)
        # 3
        tx_distribute = self._distribute()
        self.assertTrue(tx_distribute["status"], msg=pp.pformat(tx_distribute))
        # 4
        self._leave()
        owner = self._get_wallet()
        self.assertEqual(len(owner["leave_values"]), 1, msg=pp.pformat(owner))
        self.assertEqual(len(owner["unstake_heights"]), 0, msg=pp.pformat(owner))
        self.assertEqual(owner["unstaking"], hex(20 * 10 ** 18), msg=pp.pformat(owner))
        # 5
        self._increment_term_for_n(n=1)
        tx_distribute = self._distribute()
        self.assertTrue(tx_distribute["status"], msg=pp.pformat(tx_distribute))
        self.assertEqual(self._get_rewards(), hex(0))
        self.assertEqual(self._get_new_unlocked_total(), hex(0))
        self.assertEqual(self._get_total_unstaked_in_term(), hex(0))
        owner = self._get_wallet()
        self.assertEqual(len(owner["leave_values"]), len(owner["unstake_heights"]), msg=pp.pformat(owner))
        self.assertEqual(len(owner["unstake_heights"]), 1, msg=pp.pformat(owner))
        self.assertEqual(owner["unstake_heights"][0], hex(int(self._getIISSInfo()["blockHeight"], 16)
                                                          + int(self._estimateUnstakeLockPeriod()["unstakeLockPeriod"],
                                                                16)
                                                          + 300))
        self.assertEqual(owner["unstaking"], hex(20 * 10 ** 18), msg=pp.pformat(owner))
        # 6
        self._set_block_height(int(owner["unstake_heights"][0], 16))
        # 7
        tx_claim = self._claim()
        self.assertTrue(tx_claim["status"], msg=pp.pformat(tx_claim))


    def test_2_join_with_100_wallets_distribute_transfer_leave_claim(self):
        """
        1. Set iteration limit to 10, set rewards to 100 and increase cap
        2. Transfer 11 ICX to newly created wallets and make a join tx with them.
        3. Increment term on fake sys SCORE and distribute
        4. Tries to transfer between distribute calls, should fail
        5. Set i_score, create leave request for all wallets and distribute again to resolve leave them
        6. Check if the stateDB wallets are reseted
        7. Set new block height on fake System SCORE, claim back ICX and send them to original wallet
        """
        # 1
        self._set_iteration_limit(10)
        self.assertEqual(hex(10), self._get_iteration_limit(), msg=pp.pformat(self._get_iteration_limit()))
        self._set_i_score(100 * 10 ** 21)
        self.assertEqual(self._query_i_score()["iscore"], hex(100 * 10 ** 21))
        self._set_cap(1020)
        # 2
        wallets = self._n_join(100, workers=100)
        time.sleep(10)  # sleep, since sometimes happens that transaction is still not mined
        self.assertEqual(100, len(self._get_wallets()))
        # 3
        self._increment_term_for_n(n=2)
        while True:
            tx_distribute = self._distribute()
            self.assertTrue(tx_distribute["status"], msg=pp.pformat(tx_distribute))
            if not _is_distributed(tx_distribute["eventLogs"]):
                # 4
                _from: Future = wallets[0]
                _to: Future = wallets[1]
                tx_transfer = self._transfer_licx_from_to(from_=_from.result(), to=_to.result().get_address())
                self.assertFalse(tx_transfer["status"])
            else:
                break
        # 5
        self._set_i_score(100 * 10 ** 21)
        self.assertEqual(self._query_i_score()["iscore"], hex(100 * 10 ** 21))
        self._n_leave(wallets, workers=100)
        self._increment_term_for_n(n=1)
        while True:
            tx_distribute = self._distribute()
            self.assertTrue(tx_distribute["status"], msg=pp.pformat(tx_distribute))
            if _is_distributed(tx_distribute["eventLogs"]):
                break
        wallet = self._get_wallet(wallets[0].result().get_address())
        self.assertEqual(len(wallet["leave_values"]), len(wallet["unstake_heights"]), msg=pp.pformat(wallet))
        self.assertEqual(len(wallet["unstake_heights"]), 1, msg=pp.pformat(wallet))
        # 6
        self.assertEqual(self._get_rewards(), hex(0))
        self.assertEqual(self._get_new_unlocked_total(), hex(0))
        self.assertEqual(self._get_total_unstaked_in_term(), hex(0))
        # 7
        self._set_block_height(int(wallet["unstake_heights"][0], 16))
        self._n_claim(wallet_list=wallets, workers=100)

    def test_3_delete_from_linked_list(self):
        """
        1. Set rewards to 100
        2. Transfer 11 ICX to newly created wallets and make a join tx with them.
        3. Increment term on fake sys SCORE and distribute
        4. Transfer LICX, and check if the wallet was deleted from wallet's list
        5.
        """
        # 1
        self._set_i_score(100 * 10 ** 21)
        self.assertEqual(self._query_i_score()["iscore"], hex(100 * 10 ** 21))
        # 2
        wallets = self._n_join(10)
        self.assertEqual(10, len(self._get_wallets()))
        # 3
        self._increment_term_for_n(n=2)
        tx_distribute = self._distribute()
        self.assertTrue(tx_distribute["status"], msg=pp.pformat(tx_distribute))
        # 4
        from_: KeyWallet = wallets[0].result()
        to: KeyWallet = wallets[1].result()
        self._transfer_licx_from_to(from_, to.get_address(), 9.5)
        self.assertEqual(9, len(self._get_wallets()))
        self.assertEqual(hex(5 * 10 ** 17), self._balance_of(from_.get_address()))
        self.assertEqual(hex(int(19.5 * 10 ** 18)), self._balance_of(to.get_address()))
        # 5
        self._n_leave(wallet_list=wallets)
        self._increment_term_for_n(n=2)
        tx_distribute = self._distribute()
        self.assertTrue(tx_distribute["status"], msg=pp.pformat(tx_distribute))
        # 6
        wallet = self._get_wallet(wallets[1].result().get_address())
        self.assertEqual(len(wallet["leave_values"]), len(wallet["unstake_heights"]), msg=pp.pformat(wallet))
        self._set_block_height(int(wallet["unstake_heights"][0], 16))
        # 7
        self._n_claim(wallet_list=wallets, workers=100)


if __name__ == '__main__':
    unittest.main()
