import time
import unittest
import logging
import pprint
import json
import logging
import os

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.builder.transaction_builder import DeployTransactionBuilder, CallTransactionBuilder, Transaction, \
    TransactionBuilder
from iconsdk.exception import JSONRPCException
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from iconsdk.icon_service import IconService


class LiquidICXTest(unittest.TestCase):
    FORCE_DEPLOY = False  # Change to True, if you want to deploy a new SCORE for testing

    SCORE_INSTALL_ADDRESS = f"cx{'0' * 40}"
    GOV_SCORE_ADDRESS = "cx0000000000000000000000000000000000000001"

    LOCAL_NETWORK_TEST = False

    LOCAL_TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"
    LOCAL_SCORE_ADDRESS = "cxf56bb59257b412183c6ed70d7a4ed371306a98d9"

    YEUOIDO_TEST_HTTP_ENDPOINT_URI_V3 = "https://bicon.net.solidwallet.io/api/v3"
    YEUOIDO_SCORE_ADDRESS = "cx4322ccf1ad0578a8909a162b9154170859c913eb"

    pp = pprint.PrettyPrinter(indent=4)

    def setUp(self) -> None:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

        if LiquidICXTest.LOCAL_NETWORK_TEST:
            self._wallet = KeyWallet.load("../../keystore_test1", "test1_Account")
            self._icon_service = IconService(HTTPProvider(self.LOCAL_TEST_HTTP_ENDPOINT_URI_V3))
            self._score_address = LiquidICXTest.LOCAL_SCORE_ADDRESS
        else:
            self._wallet = KeyWallet.load("../../keystore_test3", "test3_Account")
            self._icon_service = IconService(HTTPProvider(self.YEUOIDO_TEST_HTTP_ENDPOINT_URI_V3))
            self._score_address = LiquidICXTest.YEUOIDO_SCORE_ADDRESS

        if LiquidICXTest.FORCE_DEPLOY:
            self._score_address = self._testDeploy()["scoreAddress"]

    def tearDown(self) -> None:
        pass

    def _getNextPrepTerm(self):
        call = self._buildTransaction(write=False,
                                      to=LiquidICXTest.SCORE_INSTALL_ADDRESS,
                                      method="getIISSInfo",
                                      params={})
        result = self._icon_service.call(call)
        # LiquidICXTest.pp.pprint(result)
        return result['nextPRepTerm']

    def _getTXResult(self, tx_hash) -> dict:
        logger = logging.getLogger('ICON-SDK-PYTHON')
        logger.disabled = True
        while True:
            try:
                res = self._icon_service.get_transaction_result(tx_hash)
                logger.disabled = False
                return res
            except JSONRPCException as e:
                if e.args[0]["message"] == "Pending transaction":
                    time.sleep(1)

    def _estimateSteps(self, margin) -> int:
        tx = self._buildTransaction(write=False, method="getStepCosts", to=LiquidICXTest.GOV_SCORE_ADDRESS, params={})
        result = self._icon_service.call(tx)
        return int(result["contractCall"], 16) + margin

    def _buildTransaction(self, write=True, method=None, params=None, **kwargs):
        if not isinstance(method, str) or not isinstance(params, dict):
            raise ValueError("Method should be string, params dictionary.")

        from_ = self._wallet.get_address() if "from" not in kwargs else kwargs["from"]
        to_ = self._score_address if "to" not in kwargs else kwargs["to"]

        if write:
            margin = 150000 if "margin" not in kwargs else kwargs["margin"]
            value = 0 if "value" not in kwargs else kwargs["value"]
            steps = self._estimateSteps(margin)

            tx = CallTransactionBuilder() \
                .from_(from_) \
                .to(to_) \
                .value(value) \
                .nid(3) \
                .step_limit(steps) \
                .nonce(100) \
                .method(method) \
                .params({}) \
                .build()
        else:
            tx = CallBuilder() \
                .to(to_) \
                .method(method) \
                .params(params) \
                .build()

        return tx

    def _testDeploy(self, deploy_address: str = SCORE_INSTALL_ADDRESS):
        dir_path = os.path.abspath(os.path.dirname(__file__))
        score_project = os.path.abspath(os.path.join(dir_path, '..'))
        score_content_bytes = gen_deploy_data_content(score_project)

        transaction = DeployTransactionBuilder() \
            .from_(self._wallet.get_address()) \
            .to(deploy_address) \
            .nid(3) \
            .step_limit(10000000000) \
            .nonce(100) \
            .content_type("application/zip") \
            .content(score_content_bytes) \
            .params({"next_term_height": self._getNextPrepTerm()}) \
            .build()

        # estimated_steps = self._estimateSteps(transaction)
        signed_transaction = SignedTransaction(transaction, self._wallet)

        tx_hash = self._icon_service.send_transaction(signed_transaction)
        tx_result = self._getTXResult(tx_hash)

        LiquidICXTest.pp.pprint(tx_result)

        self.assertEqual(True, tx_result["status"])
        self.assertTrue('scoreAddress' in tx_result)

        return tx_result

    def testUpdate(self):
        tx_result = self._testDeploy(self._score_address)
        self.assertEqual(self._score_address, tx_result['scoreAddress'])


    def testJoin(self):
        tx = self._buildTransaction(method="join", params={}, value=1)
        signed_transaction = SignedTransaction(tx, self._wallet)
        tx_hash = self._icon_service.send_transaction(signed_transaction)
        tx_result = self._getTXResult(tx_hash)
        logging.info(LiquidICXTest.pp.pprint(tx_result))
        self.assertEqual(True, tx_result["status"])

    def testGetRequests(self):
        tx = self._buildTransaction(write=False, method="getRequests", params={})
        result = self._icon_service.call(tx)
        LiquidICXTest.pp.pprint(result)

    def testHandleRequests(self):
        tx = self._buildTransaction(method="handleRequests", params={}, margin=200000)
        signed_transaction = SignedTransaction(tx, self._wallet)
        tx_hash = self._icon_service.send_transaction(signed_transaction)
        tx_result = self._getTXResult(tx_hash)
        LiquidICXTest.pp.pprint(tx_result)
        self.assertEqual(True, tx_result["status"])

    def testGetRequest(self):
        call = CallBuilder() \
            .from_(self._wallet.get_address()) \
            .to(self._score_address) \
            .method("getRequest") \
            .params({}) \
            .build()

        result = self._icon_service.call(call)
        LiquidICXTest.pp.pprint(result)

    def testClear(self):
        transaction = self._buildTransaction(method="clearRequests", params={})
        signed_transaction = SignedTransaction(transaction, self._wallet)
        tx_hash = self._icon_service.send_transaction(signed_transaction)
        tx_result = self._getTXResult(tx_hash)
        LiquidICXTest.pp.pprint(tx_result)


    def getNextTerm(self):
        call = self._buildTransaction(write=False, method="next_term", params={})
        result = self._icon_service.call(call)
        LiquidICXTest.pp.pprint(result)
        return result





if __name__ == '__main__':
    unittest.main()
