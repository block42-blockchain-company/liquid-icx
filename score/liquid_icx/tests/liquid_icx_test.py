import time
import unittest
import logging
import pprint

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

    LOCAL_NETWORK_TEST = True
    LOCAL_TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"
    LOCAL_SCORE_ADDRESS = "cx24d0ed2f7cb0b8c5a5532ba2916a2bf1cab38592"

    pp = pprint.PrettyPrinter(indent=4)

    def setUp(self) -> None:
        if LiquidICXTest.LOCAL_NETWORK_TEST:
            self._wallet = KeyWallet.load("../../keystore_test1", "test1_Account")
            self._icon_service = IconService(HTTPProvider(self.LOCAL_TEST_HTTP_ENDPOINT_URI_V3))
            self._score_address = LiquidICXTest.LOCAL_SCORE_ADDRESS
        else:
            assert ("Testing on test network not implmeneted yet.")

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
            .step_limit(1000000000) \
            .nid(3) \
            .nonce(100) \
            .content_type("application/zip") \
            .content(score_content_bytes) \
            .build()

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



if __name__ == '__main__':
    unittest.main()
