import fileinput
import os
import time
import unittest

import pprint as pp

from iconsdk.builder.transaction_builder import DeployTransactionBuilder
from iconsdk.exception import JSONRPCException
from iconsdk.icon_service import IconService
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from tbears.libs.icon_integrate_test import SCORE_INSTALL_ADDRESS
from score.liquid_icx.tests.test_integrate_base import LICXTestBase


class LiquidICXWithFakeSysSCORETest(LICXTestBase):
    LICX_FORCE_DEPLOY = True  # set to true, if you want to deploy new SCORES for each test#
    FAKE_SYS_SCORE_FORCE_DEPLOY = False  # set to true, if you want to deploy new SCORES for each test
    TERM_LENGTH = 43120

    def setUp(self):
        super().setUp()

        if self.FAKE_SYS_SCORE_FORCE_DEPLOY:
            self._fake_sys_score = self._deployFakeSystemSCORE()["scoreAddress"]
            print(f"New FAKE SYS SCORE address: {self._fake_sys_score}")

        if self.LICX_FORCE_DEPLOY:
            self.replace_in_consts_py(SCORE_INSTALL_ADDRESS, self._fake_sys_score)
            self._score_address = self._deploy_score()["scoreAddress"]
            print(f"New SCORE address: {self._score_address}")

    def tearDown(self):
        self.replace_in_consts_py(self._fake_sys_score, SCORE_INSTALL_ADDRESS)

    # -----------------------------------------------------------------------
    # ----------------------- testing helper methods ------------------------
    # -----------------------------------------------------------------------
    def _deployFakeSystemSCORE(self):
        dir_path = os.path.abspath(os.path.dirname(__file__))
        score_project = os.path.abspath(
            os.path.join(dir_path, "/Users/tomaz/Dev/Icon/LICX/liquid-icx/score/fake_system_contract"))
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

    @classmethod
    def replace_in_consts_py(cls, pattern: str, sub: str):
        for line in fileinput.input("../scorelib/consts.py", inplace=1):
            if "SYSTEM_SCORE" in line:
                line = line.replace(pattern, sub)
            print(line, end='')

    def _estimateUnstakeLockPeriod(self) -> dict:
        tx = self._build_transaction(to=self._fake_sys_score,
                                     type_="read",
                                     method="estimateUnstakeLockPeriod")
        return self.process_call(tx, self._icon_service)

    def _getPRepTerm(self) -> dict:
        tx = self._build_transaction(to=self._fake_sys_score,
                                     type_="read",
                                     method="getPRepTerm")
        return self.process_call(tx, self._icon_service)

    def _getIISSInfo(self) -> dict:
        tx = self._build_transaction(to=self._fake_sys_score,
                                     type_="read",
                                     method="getIISSInfo")
        return self.process_call(tx, self._icon_service)

    def _set_block_height(self, _new_height: int):
        paras = {
            "_new_height": _new_height
        }
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
        6. Transfer 2 LICX to wallet2
        7. Transfer 2 LICX from wallet2 back to owner's wallet
        """
        # 1
        join_value = 12
        tx_join = self._join(value=join_value)
        self.assertTrue(tx_join["status"])
        self.assertEqual(len(self._get_holders()), 1)
        # 2,3
        tx_transfer = self._transfer_from_to(self._wallet, self._wallet2.get_address())
        self.assertFalse(tx_transfer["status"], msg=pp.pformat(tx_transfer))
        self.assertEqual(tx_transfer["failure"]["message"], "LiquidICX: Out of balance.")
        owner = self._get_holder()
        self.assertEqual(len(owner["join_values"]), len(owner["unlock_heights"]))
        self.assertEqual(len(owner["join_values"]), 1)
        self.assertEqual(owner["locked"], hex(join_value * 10 ** 18))
        self.assertEqual(self._total_supply(), hex(0))
        # 4
        self._increment_term_for_n(n=2)
        # 5
        tx_distribute = self._distribute()  # user should now have unlocked licx
        self.assertTrue(tx_distribute["status"], msg=pp.pformat(tx_distribute))
        owner = self._get_holder()
        self.assertEqual(len(owner["join_values"]), len(owner["unlock_heights"]))
        self.assertEqual(len(owner["join_values"]), 0)
        self.assertEqual(owner["locked"], hex(0))
        # 6
        tx_transfer = self._transfer_from_to(self._wallet, self._wallet2.get_address(), value=2)
        self.assertTrue(tx_transfer["status"], msg=pp.pformat(tx_transfer))
        self.assertEqual(self._balance_of(self._wallet.get_address()), hex(10 * 10 ** 18))
        self.assertEqual(self._balance_of(self._wallet2.get_address()), hex(2 * 10 ** 18))
        # 7
        tx_transfer = self._transfer_from_to(self._wallet2, self._wallet.get_address(), value=2)
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
        self.assertEqual(len(self._get_holders()), 1, msg=pp.pformat(len(self._get_holders())))
        # 2
        self._increment_term_for_n(n=2)
        # 3
        tx_distribute = self._distribute()
        self.assertTrue(tx_distribute["status"], msg=pp.pformat(tx_distribute))
        # 4
        self._leave()
        owner = self._get_holder()
        self.assertEqual(len(owner["leave_values"]), 1, msg=pp.pformat(owner))
        self.assertEqual(len(owner["unstake_heights"]), 0, msg=pp.pformat(owner))
        self.assertEqual(owner["unstaking"], hex(20 * 10 ** 18), msg=pp.pformat(owner))
        # 5
        self._increment_term_for_n(n=1)
        tx_distribute = self._distribute()
        self.assertTrue(tx_distribute["status"], msg=pp.pformat(tx_distribute))
        owner = self._get_holder()
        self.assertEqual(len(owner["leave_values"]), len(owner["unstake_heights"]), msg=pp.pformat(owner))
        self.assertEqual(len(owner["unstake_heights"]), 1, msg=pp.pformat(owner))
        self.assertEqual(owner["unstake_heights"][0], hex(int(self._getIISSInfo()["blockHeight"], 16) +
                                                          int(self._estimateUnstakeLockPeriod()["unstakeLockPeriod"], 16)))
        self.assertEqual(owner["unstaking"], hex(20 * 10 ** 18), msg=pp.pformat(owner))
        # 6
        self._set_block_height(int(owner["unstake_heights"][0], 16))
        # 7
        tx_claim = self._claim()
        self.assertTrue(tx_claim["status"], msg=pp.pformat(tx_claim))



if __name__ == '__main__':
    unittest.main()