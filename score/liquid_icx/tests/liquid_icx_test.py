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

    def tearDown(self) -> None:
        pass

    def _getNextPrepTerm(self):
        call = self._buildTransaction(type="read",
                                      to=LiquidICXTest.SCORE_INSTALL_ADDRESS,
                                      method="getIISSInfo",
                                      params={})
        result = self._icon_service.call(call)
        # LiquidICXTest.pp.pprint(result)
        return result['nextPRepTerm']

    def test10Join(self):
        for it in range(0, 1):
            # create a wallet a transfer 0.1 ICX to it
            wallet = KeyWallet.create()
            tx = self._buildTransaction(type="transfer", to=wallet.get_address(), value=10**17)
            tx_hash = self._icon_service.send_transaction(SignedTransaction(tx, self._wallet))
            tx_result = self._getTXResult(tx_hash)
            self.assertEqual(True, tx_result["status"])
            # make a join request
            tx = self._buildTransaction(method="join", from_=wallet.get_address(), params={}, value=10**16)
            tx_hash = self._icon_service.send_transaction(SignedTransaction(tx, wallet))
            tx_result = self._getTXResult(tx_hash)
            logging.info(LiquidICXTest.pp.pprint(tx_result))
            self.assertEqual(True, tx_result["status"])



    def _testGetRequests(self):
        tx = self._buildTransaction(type="read", method="getRequests", params={})
        result = self._icon_service.call(tx)
        LiquidICXTest.pp.pprint(result)

    def _testHandleRequests(self):
        tx = self._buildTransaction(method="handleRequests", params={}, margin=200000)
        signed_transaction = SignedTransaction(tx, self._wallet)
        tx_hash = self._icon_service.send_transaction(signed_transaction)
        tx_result = self._getTXResult(tx_hash)
        LiquidICXTest.pp.pprint(tx_result)
        self.assertEqual(True, tx_result["status"])

    def _testGetRequest(self):
        call = CallBuilder() \
            .from_(self._wallet.get_address()) \
            .to(self._score_address) \
            .method("getRequest") \
            .params({}) \
            .build()

        result = self._icon_service.call(call)
        LiquidICXTest.pp.pprint(result)

    def _testClear(self):
        transaction = self._buildTransaction(method="clearRequests", params={})
        signed_transaction = SignedTransaction(transaction, self._wallet)
        tx_hash = self._icon_service.send_transaction(signed_transaction)
        tx_result = self._getTXResult(tx_hash)
        LiquidICXTest.pp.pprint(tx_result)


    def _getNextTerm(self):
        call = self._buildTransaction(type="read", method="next_term", params={})
        result = self._icon_service.call(call)
        LiquidICXTest.pp.pprint(result)
        return result

if __name__ == '__main__':
    unittest.main()
