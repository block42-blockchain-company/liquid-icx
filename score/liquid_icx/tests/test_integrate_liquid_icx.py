import json
import logging
import os, sys
import pprint as pp
import fileinput
from concurrent.futures.thread import ThreadPoolExecutor

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import DeployTransactionBuilder, CallTransactionBuilder, TransactionBuilder
from iconsdk.icon_service import IconService
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS

from score.liquid_icx.tests.test_integrate_base import LICXTestBase

DIR_PATH = os.path.abspath(os.path.dirname(__file__))


class LiquidICXTest(LICXTestBase):
    SCORE_PROJECT = os.path.abspath(os.path.join(DIR_PATH, '..'))

    FORCE_DEPLOY = True

    # Change to True, if you want to deploy a new SCORE for testing
    LOCAL_NETWORK_TEST = False
    TEST_WITH_FAKE_SYS_SCORE = False

    FAKE_SYS_SCORE_YEOUIDO = "cx2b01010a92bf78ee464be0b5eff94676e95cd757"

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        if LiquidICXTest.TEST_WITH_FAKE_SYS_SCORE:
            cls.replace_in_consts_py(LiquidICXTest.FAKE_SYS_SCORE_YEOUIDO, SCORE_INSTALL_ADDRESS)

    @classmethod
    def replace_in_consts_py(cls, pattern, sub):
        for line in fileinput.input("../scorelib/consts.py", inplace=1):
            if "SYSTEM_SCORE" in line:
                line = line.replace(pattern, sub)
            print(line, end='')

    def setUp(self, **kwargs):
        super().setUp()

        if LiquidICXTest.FORCE_DEPLOY:
            self._score_address = self._deploy_score()["scoreAddress"]
            print(f"New SCORE address: { self._score_address }")


    def test_score_update(self):
        # update SCORE
        if not LiquidICXTest.FORCE_DEPLOY:
            tx_result = self._deploy_score(self._score_address)
            self.assertEqual(self._score_address, tx_result['scoreAddress'], msg=pp.pformat(tx_result))

    def test_0_join_delegate_stake(self):
        self.assertEqual(self._get_holders(), [])
        self._join()
        self.assertEqual(len(self._get_holders()), 1)
        self._n_join(10)
        self.assertEqual(len(self._get_holders()), 11)
        self._join()
        self.assertEqual(len(self._get_holders()), 11)
        owner = self._get_holder()
        self.assertEqual(owner["locked"], hex(2 * 10 * 10 ** 18), msg=pp.pformat(owner))
        self.assertEqual(len(owner["join_values"]), 2, msg=pp.pformat(owner))
        self.assertEqual(len(owner["unlock_heights"]), 2, msg=pp.pformat(owner))
        self.assertEqual(self._get_staked(), hex(12 * 10 * 10 ** 18), msg=pp.pformat(owner))
        self.assertEqual(self._get_delegation()["totalDelegated"], hex(12 * 10 * 10 ** 18), msg=pp.pformat(owner))
        owner = self._get_holder()
        self.assertEqual(len(owner["join_values"]), 2, msg=pp.pformat(owner))

    def test_1_join_balance_transfer_leave(self):
        self._join(value=12)
        self.assertEqual(len(self._get_holders()), 1)
        self.assertEqual(self._balance_of(), hex(0), msg=self._balance_of())
        self.assertEqual(self._total_supply(), hex(0), msg=self._total_supply())
        transfer_tx = self._transfer_from_to(self._wallet, to=self._wallet2.get_address())
        self.assertEqual(transfer_tx["status"], 0, msg=pp.pformat(transfer_tx))
        self.assertEqual(transfer_tx["failure"]["message"], "LiquidICX: Out of balance.")
        self.assertEqual(self._balance_of(), hex(0), msg=self._balance_of())
        leave_tx = self._leave(5)
        self.assertEqual(leave_tx["status"], 0, msg=pp.pformat(leave_tx))
        self.assertIn("Leaving value cannot be less than", leave_tx["failure"]["message"], msg=pp.pformat(leave_tx))
        leave_tx = self._leave(11)
        self.assertEqual(leave_tx["status"], 0, msg=pp.pformat(leave_tx))
        self.assertEqual(leave_tx["failure"]["message"], "LiquidICX: Out of balance.", msg=pp.pformat(leave_tx))
        owner = self._get_holder()
        self.assertEqual(owner["locked"], hex(12 * 10 ** 18), msg=pp.pformat(owner))
        self.assertEqual(owner["unstaking"], hex(0), msg=pp.pformat(owner))

    def _join_with_new_created_wallet(self):
        # create a wallet and transfer 11 ICX to it
        wallet = KeyWallet.create()
        tx = self._build_transaction(type_="transfer", to=wallet.get_address(), value=11 * 10 ** 18)
        tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
        self.assertEqual(True, tx_result["status"], msg=pp.pformat(tx_result))
        # make a join request
        tx = self._build_transaction(method="join", from_=wallet.get_address(), params={}, value=10 * 10 ** 18)
        tx_result = self.process_transaction(SignedTransaction(tx, wallet), self._icon_service)
        self.assertEqual(True, tx_result["status"], msg=pp.pformat(tx_result))
        return tx_result

    def _n_join(self, n: int = 10, workers: int = 10):
        result = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for it in range(0, n):
                tx_res = pool.submit(self._join_with_new_created_wallet)
                result.append(tx_res)
