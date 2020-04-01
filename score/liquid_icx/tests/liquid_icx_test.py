import time
import unittest
import logging

from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.builder.transaction_builder import DeployTransactionBuilder
from iconsdk.exception import JSONRPCException
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from iconsdk.icon_service import IconService



class LiquidICXTest(unittest.TestCase):
    LOCAL_NETWORK_TEST = True
    LOCAL_TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"
    SCORE_INSTALL_ADDRESS = f"cx{'0' * 40}"

    def setUp(self) -> None:
        if LiquidICXTest.LOCAL_NETWORK_TEST:
            self._wallet = KeyWallet.load("../../keystore_test1", "test1_Account")
            self._icon_service = IconService(HTTPProvider(self.LOCAL_TEST_HTTP_ENDPOINT_URI_V3))
        else:
            assert ("Testing on test network not implmeneted yet.")

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


if __name__ == '__main__':
    unittest.main()
