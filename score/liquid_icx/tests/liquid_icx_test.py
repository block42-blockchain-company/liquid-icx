import time
import unittest
import logging
import pprint
import json

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.builder.transaction_builder import DeployTransactionBuilder, CallTransactionBuilder, Transaction
from iconsdk.exception import JSONRPCException
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from iconsdk.icon_service import IconService


class LiquidICXTest(unittest.TestCase):
    FORCE_DEPLOY = False  # Change to True, if you want to deploy a new SCORE for testing
    SCORE_INSTALL_ADDRESS = f"cx{'0' * 40}"

    LOCAL_NETWORK_TEST = False

    LOCAL_TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"
    LOCAL_SCORE_ADDRESS = "cxf56bb59257b412183c6ed70d7a4ed371306a98d9"

    YEUOIDO_TEST_HTTP_ENDPOINT_URI_V3 = "https://bicon.net.solidwallet.io/api/v3"
    YEUOIDO_SCORE_ADDRESS = "cx4322ccf1ad0578a8909a162b9154170859c913eb"

    pp = pprint.PrettyPrinter(indent=4)

    def setUp(self) -> None:
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

    def _getTXResult(self, tx_hash) -> dict:
        while True:
            try:
                return self._icon_service.get_transaction_result(tx_hash)
            except JSONRPCException as e:
                if e.args[0]["message"] == "Pending transaction":
                    time.sleep(1)

    def _estimateSteps(self, tx: Transaction, margin: int = 10000):
        return self._icon_service.estimate_step(tx) + margin

    def _testDeploy(self, deploy_address: str = SCORE_INSTALL_ADDRESS):
        score_content_bytes = gen_deploy_data_content("../")

        transaction = DeployTransactionBuilder() \
            .from_(self._wallet.get_address()) \
            .to(deploy_address) \
            .nid(3) \
            .step_limit(10000000000) \
            .nonce(100) \
            .content_type("application/zip") \
            .content(score_content_bytes) \
            .build()

        #estimated_steps = self._estimateSteps(transaction)
        signed_transaction = SignedTransaction(transaction, self._wallet)

        tx_hash = self._icon_service.send_transaction(signed_transaction)
        tx_result = self._getTXResult(tx_hash)

        self.assertEqual(True, tx_result["status"])
        self.assertTrue('scoreAddress' in tx_result)

        return tx_result

    def testUpdate(self):
        tx_result = self._testDeploy(self._score_address)
        self.assertEqual(self._score_address, tx_result['scoreAddress'])

    def testDeposit(self):
        transaction = CallTransactionBuilder() \
            .from_(self._wallet.get_address()) \
            .to(self._score_address) \
            .value(100) \
            .nid(3) \
            .nonce(100) \
            .step_limit(100000000) \
            .method("deposit") \
            .params({}) \
            .build()

        # step_limit = self._estimateSteps(transaction)
        signed_transaction = SignedTransaction(transaction, self._wallet)

        tx_hash = self._icon_service.send_transaction(signed_transaction)
        tx_result = self._getTXResult(tx_hash)

        self.assertEqual(True, tx_result["status"])
        self.assertEqual(2, len(tx_result["eventLogs"]))

        # There should be always exactly 2 events fired at the deposit
        for log in tx_result["eventLogs"]:
            event_name = log["indexed"][0]
            self.assertTrue("Transfer(Address,Address,int,bytes)" == event_name or
                            "ICXTransfer(Address,Address,int)" == event_name)


    def testJoin(self):
        transaction = CallTransactionBuilder() \
            .from_(self._wallet.get_address()) \
            .to(self._score_address) \
            .value(1) \
            .nid(3) \
            .nonce(100) \
            .step_limit(100000000) \
            .method("join") \
            .params({}) \
            .build()

        # step_limit = self._estimateSteps(transaction)
        signed_transaction = SignedTransaction(transaction, self._wallet)

        tx_hash = self._icon_service.send_transaction(signed_transaction)
        tx_result = self._getTXResult(tx_hash)
        LiquidICXTest.pp.pprint(tx_result)

    def testGetRequests(self):
        call = CallBuilder() \
            .to(self._score_address) \
            .method("getRequests") \
            .params({}) \
            .build()

        result = self._icon_service.call(call)
        LiquidICXTest.pp.pprint(result)

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
        transaction = CallTransactionBuilder() \
            .from_(self._wallet.get_address()) \
            .to(self._score_address) \
            .nid(3) \
            .nonce(100) \
            .step_limit(100000000) \
            .method("clearRequests") \
            .params({}) \
            .build()

        # step_limit = self._estimateSteps(transaction)
        signed_transaction = SignedTransaction(transaction, self._wallet)

        tx_hash = self._icon_service.send_transaction(signed_transaction)
        tx_result = self._getTXResult(tx_hash)
        LiquidICXTest.pp.pprint(tx_result)


    def testgetPrepTerm(self):

        call = CallBuilder() \
            .from_(self._wallet.get_address()) \
            .to(LiquidICXTest.SCORE_INSTALL_ADDRESS) \
            .method("getIISSInfo") \
            .params({}) \
            .build()

        result = self._icon_service.call(call)
        LiquidICXTest.pp.pprint(result)




if __name__ == '__main__':
    unittest.main()
