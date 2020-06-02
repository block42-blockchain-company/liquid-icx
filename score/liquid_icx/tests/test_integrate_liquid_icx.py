import json
import logging
import os
import pprint

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

    SCORE_PROJECT= os.path.abspath(os.path.join(DIR_PATH, '..'))

    FORCE_DEPLOY = False  # Change to True, if you want to deploy a new SCORE for testing

    GOV_SCORE_ADDRESS = "cx0000000000000000000000000000000000000001"

    LOCAL_NETWORK_TEST = False

    LOCAL_TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"
    LOCAL_SCORE_ADDRESS = "cxf56bb59257b412183c6ed70d7a4ed371306a98d9"

    YEUOIDO_TEST_HTTP_ENDPOINT_URI_V3 = "https://bicon.net.solidwallet.io/api/v3"
    YEUOIDO_SCORE_ADDRESS = "cx4322ccf1ad0578a8909a162b9154170859c913eb"

    pp = pprint.PrettyPrinter(indent=4)

    def setUp(self):
        super().setUp()

        if LiquidICXTest.LOCAL_NETWORK_TEST:
            self._wallet = KeyWallet.load("../../keystore_test1", "test1_Account")
            self._icon_service = None
            self._score_address = LiquidICXTest.LOCAL_SCORE_ADDRESS
        else:
            self._wallet = KeyWallet.load("../../keystore_test3", "test3_Account")
            self._icon_service = IconService(HTTPProvider(self.YEUOIDO_TEST_HTTP_ENDPOINT_URI_V3))
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
            .params({"next_term_height": self._get_next_prep_term()}) \
            .build()

        # Returns the signed transaction object having a signature
        signed_transaction = SignedTransaction(transaction, self._wallet)

        # process the transaction in local
        tx_result = self.process_transaction(signed_transaction, self._icon_service)

        self.assertEqual(True, tx_result['status'])
        self.assertTrue('scoreAddress' in tx_result)

        return tx_result

    def test_score_update(self):
        # update SCORE
        tx_result = self._deploy_score(self._score_address)
        self.assertEqual(self._score_address, tx_result['scoreAddress'])

    def _get_next_prep_term(self):
        call = self._build_transaction(type_="read",
                                       to=SCORE_INSTALL_ADDRESS,
                                       method="getIISSInfo",
                                       params={})
        result = self._icon_service.call(call)
        return result['nextPRepTerm']

    def _estimate_steps(self, margin) -> int:
        tx = self._build_transaction(type_="read", method="getStepCosts", to=LiquidICXTest.GOV_SCORE_ADDRESS, params={})
        result = self._icon_service.call(tx)
        return int(result["contractCall"], 16) + margin

    def _build_transaction(self, type_="write", **kwargs):
        if type_ not in ("transfer", "write", "read"):
            raise ValueError("Wrong type value")

        from_ = self._wallet.get_address() if "from_" not in kwargs else kwargs["from_"]
        to_ = self._score_address if "to" not in kwargs else kwargs["to"]
        margin_ = 150000 if "margin" not in kwargs else kwargs["margin"]
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
                .to(to_) \
                .method(method_) \
                .params({}) \
                .build()
        elif type_ == "transfer":
            steps_ = self._estimate_steps(margin_)
            tx = TransactionBuilder()\
                .from_(from_)\
                .to(to_)\
                .value(value_) \
                .step_limit(steps_) \
                .nid(3) \
                .build()

        return tx

    def test_join(self):
        tx = self._build_transaction(method="join", value=1)
        signed_transaction = SignedTransaction(tx, self._wallet)
        tx_result = self.process_transaction(signed_transaction, self._icon_service)
        self.assertEqual(True, tx_result["status"], msg=LiquidICXTest.pp.pformat(tx_result))

    def test_10_join(self):
        for it in range(0, 10):
            # create a wallet and transfer 0.1 ICX to it
            wallet = KeyWallet.create()
            tx = self._build_transaction(type_="transfer", to=wallet.get_address(), value=10 ** 17)
            tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
            self.assertEqual(True, tx_result["status"], msg=LiquidICXTest.pp.pformat(tx_result))
            # make a join request
            tx = self._build_transaction(method="join", from_=wallet.get_address(), params={}, value=10**16)
            tx_result = self.process_transaction(SignedTransaction(tx, wallet), self._icon_service)
            self.assertEqual(True, tx_result["status"], msg=LiquidICXTest.pp.pformat(tx_result))

    def test_get_holders(self):
        tx = self._build_transaction(method="getHolders", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)
        # self.assertEqual(True, tx_result["status"], msg=LiquidICXTest.pp.pformat(tx_result))


