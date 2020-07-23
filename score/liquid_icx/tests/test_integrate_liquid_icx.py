import json
import logging
import os
import pprint
from concurrent.futures.thread import ThreadPoolExecutor

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import DeployTransactionBuilder, CallTransactionBuilder, TransactionBuilder
from iconsdk.icon_service import IconService
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS

DIR_PATH = os.path.abspath(os.path.dirname(__file__))


class LiquidICXTest(IconIntegrateTestBase):
    SCORE_PROJECT = os.path.abspath(os.path.join(DIR_PATH, '..'))

    FORCE_DEPLOY = False  # Change to True, if you want to deploy a new SCORE for testing

    GOV_SCORE_ADDRESS = "cx0000000000000000000000000000000000000001"

    LOCAL_NETWORK_TEST = False

    LOCAL_TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"
    LOCAL_SCORE_ADDRESS = "cx77c06488a0b5567e881585d9336953bad22193ea"

    YEUOIDO_TEST_HTTP_ENDPOINT_URI_V3 = "https://bicon.net.solidwallet.io/api/v3"
    YEUOIDO_SCORE_ADDRESS = "cxfc51501665c72c26cb01ae009bbd1eddf0c79e4b"

    pp = pprint.PrettyPrinter(indent=4)

    def setUp(self):
        super().setUp()

        if LiquidICXTest.LOCAL_NETWORK_TEST:
            self._wallet = KeyWallet.load("../../keystore_test1", "test1_Account")
            self._icon_service = IconService(HTTPProvider(LiquidICXTest.LOCAL_TEST_HTTP_ENDPOINT_URI_V3))
            self._score_address = LiquidICXTest.LOCAL_SCORE_ADDRESS
        else:
            self._wallet = KeyWallet.load("../../keystore_test3", "test3_Account")
            self._wallet2 = KeyWallet.load("../../keystore_test1", "test1_Account")
            self._icon_service = IconService(HTTPProvider(LiquidICXTest.YEUOIDO_TEST_HTTP_ENDPOINT_URI_V3))
            self._score_address = LiquidICXTest.YEUOIDO_SCORE_ADDRESS

        if LiquidICXTest.FORCE_DEPLOY:
            self._score_address = self._deploy_score()["scoreAddress"]

    def _deploy_score(self, to: str = SCORE_INSTALL_ADDRESS) -> dict:
        score_content_bytes = gen_deploy_data_content(LiquidICXTest.SCORE_PROJECT)

        # Generates an instance of transaction for deploying SCORE.
        transaction = DeployTransactionBuilder() \
            .from_(self._wallet.get_address()) \
            .to(to) \
            .nid(3) \
            .step_limit(10000000000) \
            .nonce(100) \
            .content_type("application/zip") \
            .content(score_content_bytes) \
            .params({}) \
            .build()

        # Returns the signed transaction object having a signature
        signed_transaction = SignedTransaction(transaction, self._wallet)

        # process the transaction in local
        tx_result = self.process_transaction(signed_transaction, self._icon_service)

        self.assertEqual(True, tx_result['status'], msg=LiquidICXTest.pp.pformat(tx_result))
        self.assertTrue('scoreAddress' in tx_result, msg=LiquidICXTest.pp.pformat(tx_result))

        if LiquidICXTest.FORCE_DEPLOY:
            print(f"New SCORE address: {tx_result['scoreAddress']}")

        return tx_result

    def _estimate_steps(self, margin) -> int:
        tx = self._build_transaction(type_="read", method="getStepCosts", to=LiquidICXTest.GOV_SCORE_ADDRESS, params={})
        result = self._icon_service.call(tx)
        return int(result["contractCall"], 16) + margin

    def _build_transaction(self, type_="write", **kwargs):
        if type_ not in ("transfer", "write", "read"):
            raise ValueError("Wrong type value")

        from_ = self._wallet.get_address() if "from_" not in kwargs else kwargs["from_"]
        to_ = self._score_address if "to" not in kwargs else kwargs["to"]
        margin_ = 2500000 if "margin" not in kwargs else kwargs["margin"]
        value_ = 0 if "value" not in kwargs else kwargs["value"]
        method_ = None if "method" not in kwargs else kwargs["method"]
        params_ = {} if "params" not in kwargs else kwargs["params"]

        if type_ == "write":
            steps_ = self._estimate_steps(margin_)
            tx = CallTransactionBuilder() \
                .from_(from_) \
                .to(to_) \
                .value(value_) \
                .nid(3) \
                .step_limit(steps_) \
                .nonce(100) \
                .method(method_) \
                .params(params_) \
                .build()
        elif type_ == "read":
            tx = CallBuilder() \
                .from_(from_) \
                .to(to_) \
                .method(method_) \
                .params(params_) \
                .build()
        elif type_ == "transfer":
            steps_ = self._estimate_steps(margin_)
            tx = TransactionBuilder() \
                .from_(from_) \
                .to(to_) \
                .value(value_) \
                .step_limit(steps_) \
                .nid(3) \
                .build()

        return tx

    def _get_next_prep_term_IISS(self):
        call = self._build_transaction(type_="read",
                                       to=SCORE_INSTALL_ADDRESS,
                                       method="getIISSInfo",
                                       params={})
        result = dict()
        if LiquidICXTest.LOCAL_NETWORK_TEST:
            self._icon_service = IconService(HTTPProvider(LiquidICXTest.YEUOIDO_TEST_HTTP_ENDPOINT_URI_V3))
            result = self._icon_service.call(call)
            self._icon_service = IconService(HTTPProvider(LiquidICXTest.LOCAL_TEST_HTTP_ENDPOINT_URI_V3))
        else:
            result = self._icon_service.call(call)
        return result['nextPRepTerm']

    def test_score_update(self):
        # update SCORE
        if not LiquidICXTest.FORCE_DEPLOY:
            tx_result = self._deploy_score(self._score_address)
            self.assertEqual(self._score_address, tx_result['scoreAddress'], msg=LiquidICXTest.pp.pformat(tx_result))

    def test_set_next_prep_term(self):
        paras = {"_next_term": int(self._get_next_prep_term_IISS(), 16) + (43120 * 2)}
        tx = self._build_transaction(method="setNextTerm", params=paras)
        signed_transaction = SignedTransaction(tx, self._wallet)
        tx_result = self.process_transaction(signed_transaction, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)

    def test_get_next_prep_term(self):
        tx = self._build_transaction(method="nextTerm", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)

    def test_join(self):
        tx = self._build_transaction(method="join", value=1)
        signed_transaction = SignedTransaction(tx, self._wallet)
        tx_result = self.process_transaction(signed_transaction, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)
        self.assertEqual(True, tx_result["status"], msg=LiquidICXTest.pp.pformat(tx_result))

    def _join_with_new_wallet(self):
        # create a wallet and transfer 0.1 ICX to it
        wallet = KeyWallet.create()
        tx = self._build_transaction(type_="transfer", to=wallet.get_address(), value=10 ** 17)
        tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
        self.assertEqual(True, tx_result["status"], msg=LiquidICXTest.pp.pformat(tx_result))
        # make a join request
        tx = self._build_transaction(method="join", from_=wallet.get_address(), params={}, value=10 ** 16)
        tx_result = self.process_transaction(SignedTransaction(tx, wallet), self._icon_service)
        self.assertEqual(True, tx_result["status"], msg=LiquidICXTest.pp.pformat(tx_result))
        return tx_result

    def test_10000_join(self):
        result = []
        with ThreadPoolExecutor(max_workers=100) as pool:
            for it in range(0, 10000):
                tx_res = pool.submit(self._join_with_new_wallet)
                result.append(tx_res)
        self.assertEqual(10, len(self.test_get_holders()))

    def test_join_with_new_wallet(self):
        self._join_with_new_wallet()

    def test_get_holders(self):
        tx = self._build_transaction(method="getHolders", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)
        self.assertEqual(True, tx_result["status"], msg=LiquidICXTest.pp.pformat(tx_result))
        return tx_result

    def test_get_holder(self):
        tx = self._build_transaction(method="getHolder", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)

    def test_transfer(self):
        paras = {
            "_to": self._wallet2.get_address(),
            "_value": 1
        }
        tx = self._build_transaction(method="transfer", params=paras)
        tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)

    def test_remove_holder(self):
        pass
        tx = self._build_transaction(method="removeHolder")
        tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)

    def test_balance_of(self):
        paras = {"_owner": self._wallet.get_address()}
        tx = self._build_transaction(method="balanceOf", params=paras, type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)

    def test_total_supply(self):
        tx = self._build_transaction(method="totalSupply", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)

    def test_unlock_holder_licx(self):
        tx = self._build_transaction(method="unlockHolderLicx", type_="write", margin=5000000)
        tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)

    def test_get_arrays_count(self):
        tx = self._build_transaction(method="arraysCounts", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)

    def test_test(self):
        tx = self._build_transaction(method="blabla", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)
