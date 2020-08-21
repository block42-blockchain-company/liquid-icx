import re
import unittest
import pprint
import logging
import fileinput
import time
import random

from iconsdk.exception import JSONRPCException
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.icon_service import IconService
from tbears.libs.icon_integrate_test import IconIntegrateTestBase

from .utils2 import *
from .utils2 import _buildTransaction, _testDeploy, _getBalance, _getTransferable, _getLocked, _join, \
    _getIISSInfo, _getPRepTerm, _incrementTerm, _distribute, _assertBalancesEqual, _transfer, _getHolders, \
    _joinDontWaitForTxResult, _setIterationLimit, _getIterationLimit
from ..scorelib.consts import *


class LiquidICXTest(IconIntegrateTestBase):
    LOCAL_NETWORK_TEST = True
    _wallets = []

    LOCAL_TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"
    YEUOIDO_TEST_HTTP_ENDPOINT_URI_V3 = "https://bicon.net.solidwallet.io/api/v3"
    MIN_VALUE_TO_GET_REWARDS = 10 * 10 ** 18

    pp = pprint.PrettyPrinter(indent=4)

    # Gets executed before the whole Testsuite
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

        if LiquidICXTest.LOCAL_NETWORK_TEST:
            testing_wallet = cls._test1
            cls._icon_service = IconService(HTTPProvider(cls.LOCAL_TEST_HTTP_ENDPOINT_URI_V3))
        else:
            yeouido_wallet_path = os.environ['TESTNET_WALLET_PATH']
            yeouido_wallet_password = os.environ['TESTNET_WALLET_PASSWORD']
            testing_wallet = KeyWallet.load(yeouido_wallet_path, yeouido_wallet_password)
            cls._icon_service = IconService(HTTPProvider(cls.YEUOIDO_TEST_HTTP_ENDPOINT_URI_V3))

        # Set up wallets
        cls._wallets.append(testing_wallet)
        for i in range(1005):
            if i < len(cls._wallet_array):
                new_wallet = cls._wallet_array[i]
            else:
                new_wallet = KeyWallet.create()
            cls._wallets.append(new_wallet)

            licx_test = LiquidICXTest()
            tx = _buildTransaction(licx_test, type="transfer", value=cls.MIN_VALUE_TO_GET_REWARDS * 1,
                                   from_=cls._wallets[0].get_address(), _to=cls._wallets[i].get_address())
            signed_transaction = SignedTransaction(tx, cls._wallets[0])
            cls._icon_service.send_transaction(signed_transaction)

        cls.deployFakeSystemSCORE()
        cls.replaceInConsts(cls._score_address_fake_system_score)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls.replaceInConsts(SCORE_INSTALL_ADDRESS)

    @classmethod
    def deployFakeSystemSCORE(cls):
        dir_path = os.path.abspath(os.path.dirname(__file__))
        score_project = os.path.abspath(os.path.join(dir_path, "../../fake_system_contract"))
        score_content_bytes = gen_deploy_data_content(score_project)

        transaction = DeployTransactionBuilder() \
            .from_(cls._wallets[0].get_address()) \
            .to(SCORE_INSTALL_ADDRESS) \
            .nid(3) \
            .step_limit(10000000000) \
            .nonce(100) \
            .content_type("application/zip") \
            .content(score_content_bytes) \
            .params({}) \
            .build()

        signed_transaction = SignedTransaction(transaction, cls._wallets[0])
        tx_hash = cls._icon_service.send_transaction(signed_transaction)
        while True:
            try:
                tx_result = cls._icon_service.get_transaction_result(tx_hash)
                cls.pp.pprint(tx_result)
                break
            except JSONRPCException as e:
                if e.args[0]["message"] == "Pending transaction":
                    time.sleep(1)
        assert True == tx_result["status"], "Deploying the Fake System SCORE failed!"
        cls._score_address_fake_system_score = tx_result["scoreAddress"]

    @classmethod
    def replaceInConsts(cls, sub):
        print(os.getcwd())
        path = "scorelib/consts.py" if "liquid_icx" in os.getcwd() else "liquid_icx/scorelib/consts.py"
        for line in fileinput.input(path, inplace=1):
            if "SYSTEM_SCORE" in line:
                line = "SYSTEM_SCORE = Address.from_string('" + sub + "')\n"
                #line = re.sub(r'"[^"]*"', "'" + sub + "'", line)
            print(line, end='')

    # Gets executed before each Testcase
    def setUp(self) -> None:
        super().setUp()
        self._score_address_licx = _testDeploy(self, relative_score_path="../", _from=self._wallets[0])["scoreAddress"]

    #################################################################################################################
    # TEST CASES
    #################################################################################################################

    def testUpdate(self):
        tx_result = _testDeploy(self, relative_score_path="../", _from=self._wallets[0],
                                     deploy_address=self._score_address_licx)
        self.assertEqual(self._score_address_licx, tx_result['scoreAddress'],
                         "Updating the LICX SCORE failed!")

    def testIncrementTerm(self):
        current_nextPRepTerm = int(_getIISSInfo(self)['nextPRepTerm'], 16)
        current_startBlockHeight = int(_getPRepTerm(self)['startBlockHeight'], 16)

        for i in range(1, 5):
            _incrementTerm(self, self._wallets[0])

            self.assertEqual(int(_getIISSInfo(self)['nextPRepTerm'], 16), current_nextPRepTerm + TERM_LENGTH * i, "nextPRepTerm returns wrong value!")
            self.assertEqual(int(_getPRepTerm(self)['startBlockHeight'], 16), current_startBlockHeight + TERM_LENGTH * i, "startBlockHeight returns wrong value!")

    def testSingleWalletJoin(self):
        _assertBalancesEqual(self, self._wallets[0].get_address(), 0, 0, 0)

        tx_result = _join(self, self._wallets[0], self.MIN_VALUE_TO_GET_REWARDS)

        self.assertEqual(tx_result["status"], True, "Join TX should succeed but did not!")
        _assertBalancesEqual(self, self._wallets[0].get_address(), 0, 0, self.MIN_VALUE_TO_GET_REWARDS)

        _incrementTerm(self, self._wallets[0])
        _incrementTerm(self, self._wallets[0])
        
        _distribute(self, self._wallets[0])
        _assertBalancesEqual(self, self._wallets[0].get_address(), self.MIN_VALUE_TO_GET_REWARDS, self.MIN_VALUE_TO_GET_REWARDS, 0)

    def test1005WalletsJoin(self):
        for i in range(1004):
            _joinDontWaitForTxResult(self, self._wallets[i], self.MIN_VALUE_TO_GET_REWARDS)
        _join(self, self._wallets[1004], self.MIN_VALUE_TO_GET_REWARDS)

        _incrementTerm(self, self._wallets[0])
        _incrementTerm(self, self._wallets[0])
        _distribute(self, self._wallets[0])
        _distribute(self, self._wallets[0])
        _distribute(self, self._wallets[0])

        self.assertEqual(len(_getHolders(self)), 1005, "Not all joined wallets are in holders!")
        _assertBalancesEqual(self, self._wallets[random.randrange(1005)].get_address(), self.MIN_VALUE_TO_GET_REWARDS, self.MIN_VALUE_TO_GET_REWARDS, 0)
        _assertBalancesEqual(self, self._wallets[random.randrange(1005)].get_address(), self.MIN_VALUE_TO_GET_REWARDS, self.MIN_VALUE_TO_GET_REWARDS, 0)
        _assertBalancesEqual(self, self._wallets[random.randrange(1005)].get_address(), self.MIN_VALUE_TO_GET_REWARDS, self.MIN_VALUE_TO_GET_REWARDS, 0)

    def testJoinSingleWalletMultipleTimes(self):
        for i in range(3):
            tx_result = _join(self, self._wallets[0], self.MIN_VALUE_TO_GET_REWARDS)
            self.assertEqual(tx_result["status"], True, "Join TX should succeed but did not!")

        _assertBalancesEqual(self, self._wallets[0].get_address(), 0, 0, self.MIN_VALUE_TO_GET_REWARDS * 3)
        _incrementTerm(self, self._wallets[0])

        for i in range(4):
            tx_result = _join(self, self._wallets[0], self.MIN_VALUE_TO_GET_REWARDS)
            self.assertEqual(tx_result["status"], True, "Join TX should succeed but did not!")

        _assertBalancesEqual(self, self._wallets[0].get_address(), 0, 0, self.MIN_VALUE_TO_GET_REWARDS * 7)
        _incrementTerm(self, self._wallets[0])

        _distribute(self, self._wallets[0])
        _assertBalancesEqual(self, self._wallets[0].get_address(), self.MIN_VALUE_TO_GET_REWARDS * 3, self.MIN_VALUE_TO_GET_REWARDS * 3, self.MIN_VALUE_TO_GET_REWARDS * 4)

        _incrementTerm(self, self._wallets[0])
        _distribute(self, self._wallets[0])

        self.assertGreater(_getBalance(self, self._wallets[0].get_address()), self.MIN_VALUE_TO_GET_REWARDS * 7, "Balance should be greater but is not!")
        self.assertGreater(_getTransferable(self, self._wallets[0].get_address()), self.MIN_VALUE_TO_GET_REWARDS * 7, "Transferable should be greater but is not!")
        self.assertEqual(_getLocked(self, self._wallets[0].get_address()), 0, "Locked has the wrong value!")

    def testJoinFailMoreThan10Joins(self):
        for i in range(6):
            tx_result = _join(self, self._wallets[0], self.MIN_VALUE_TO_GET_REWARDS)
            self.assertEqual(tx_result["status"], True, "Join TX should succeed but did not!")

        _assertBalancesEqual(self, self._wallets[0].get_address(), 0, 0, self.MIN_VALUE_TO_GET_REWARDS * 6)
        _incrementTerm(self, self._wallets[0])

        for i in range(4):
            tx_result = _join(self, self._wallets[0], self.MIN_VALUE_TO_GET_REWARDS)
            self.assertEqual(tx_result["status"], True, "Join TX should succeed but did not!")

        _assertBalancesEqual(self, self._wallets[0].get_address(), 0, 0, self.MIN_VALUE_TO_GET_REWARDS * 10)

        for i in range(2):
            tx_result = _join(self, self._wallets[0], self.MIN_VALUE_TO_GET_REWARDS)
            self.assertEqual(tx_result["status"], False, "Join TX should fail but did not!")

        _incrementTerm(self, self._wallets[0])
        _distribute(self, self._wallets[0])
        _assertBalancesEqual(self, self._wallets[0].get_address(), self.MIN_VALUE_TO_GET_REWARDS * 6, self.MIN_VALUE_TO_GET_REWARDS * 6, self.MIN_VALUE_TO_GET_REWARDS * 4)
        _incrementTerm(self, self._wallets[0])
        _distribute(self, self._wallets[0])
        self.assertGreater(_getBalance(self, self._wallets[0].get_address()), self.MIN_VALUE_TO_GET_REWARDS * 10, "Balance should be greater but is not!")
        self.assertGreater(_getTransferable(self, self._wallets[0].get_address()), self.MIN_VALUE_TO_GET_REWARDS * 10, "Transferable should be greater but is not!")
        self.assertEqual(_getLocked(self, self._wallets[0].get_address()), 0, "Locked has the wrong value!")

    def testJoinFailLessThanMinValue(self):
        tx_result = _join(self, self._wallets[0], self.MIN_VALUE_TO_GET_REWARDS - 10000)
        self.assertEqual(tx_result["status"], False, "Join TX should fail but did not!")

        tx_result = _join(self, self._wallets[0], self.MIN_VALUE_TO_GET_REWARDS - 1)
        self.assertEqual(tx_result["status"], False, "Join TX should fail but did not!")

    def testSingleWalletDistribute(self):
        _join(self, self._wallets[0], self.MIN_VALUE_TO_GET_REWARDS)
        _assertBalancesEqual(self, self._wallets[0].get_address(), 0, 0, self.MIN_VALUE_TO_GET_REWARDS)

        _incrementTerm(self, self._wallets[0])
        _incrementTerm(self, self._wallets[0])

        tx_result = _distribute(self, self._wallets[0])

        self.assertEqual(tx_result["status"], True, "Distribute TX should succeed but did not!")
        _assertBalancesEqual(self, self._wallets[0].get_address(), self.MIN_VALUE_TO_GET_REWARDS, self.MIN_VALUE_TO_GET_REWARDS, 0)
        _incrementTerm(self, self._wallets[0])

        tx_result = _distribute(self, self._wallets[0])

        self.assertEqual(tx_result["status"], True, "Distribute TX should succeed but did not!")
        self.assertGreater(_getBalance(self, self._wallets[0].get_address()), self.MIN_VALUE_TO_GET_REWARDS, "Balance should be greater but is not!")
        self.assertGreater(_getTransferable(self, self._wallets[0].get_address()), self.MIN_VALUE_TO_GET_REWARDS, "Transferable should be greater but is not!")
        self.assertEqual(_getLocked(self, self._wallets[0].get_address()), 0, "Locked has the wrong value!")

    def test1005WalletsDistribute(self):
        for i in range(1004):
            _joinDontWaitForTxResult(self, self._wallets[i], self.MIN_VALUE_TO_GET_REWARDS)
        _join(self, self._wallets[1004], self.MIN_VALUE_TO_GET_REWARDS)

        _incrementTerm(self, self._wallets[0])
        _incrementTerm(self, self._wallets[0])
        tx_result1 = _distribute(self, self._wallets[0])
        tx_result2 = _distribute(self, self._wallets[0])
        tx_result3 = _distribute(self, self._wallets[0])

        self.assertEqual(tx_result1["status"], True, "Distribute TX should succeed but did not!")
        self.assertEqual(tx_result2["status"], True, "Distribute TX should succeed but did not!")
        self.assertEqual(tx_result3["status"], True, "Distribute TX should succeed but did not!")

        self.assertEqual(len(_getHolders(self)), 1005, "Not all joined wallets are in holders!")
        _assertBalancesEqual(self, self._wallets[random.randrange(1005)].get_address(), self.MIN_VALUE_TO_GET_REWARDS, self.MIN_VALUE_TO_GET_REWARDS, 0)

        _incrementTerm(self, self._wallets[0])
        tx_result1 = _distribute(self, self._wallets[0])
        tx_result2 = _distribute(self, self._wallets[0])
        tx_result3 = _distribute(self, self._wallets[0])

        self.assertEqual(tx_result1["status"], True, "Distribute TX should succeed but did not!")
        self.assertEqual(tx_result2["status"], True, "Distribute TX should succeed but did not!")
        self.assertEqual(tx_result3["status"], True, "Distribute TX should succeed but did not!")

        self.assertEqual(len(_getHolders(self)), 1005, "Not all joined wallets are in holders!")
        self.assertGreater(_getBalance(self, self._wallets[random.randrange(1005)].get_address()), self.MIN_VALUE_TO_GET_REWARDS, "Balance should be greater but is not!")
        self.assertGreater(_getTransferable(self, self._wallets[random.randrange(1005)].get_address()), self.MIN_VALUE_TO_GET_REWARDS, "Transferable should be greater but is not!")
        self.assertEqual(_getLocked(self, self._wallets[random.randrange(1005)].get_address()), 0, "Locked has the wrong value!")

    def testMultipleDistributeIterations(self):
        _join(self, self._wallets[0], self.MIN_VALUE_TO_GET_REWARDS)
        _assertBalancesEqual(self, self._wallets[0].get_address(), 0, 0, self.MIN_VALUE_TO_GET_REWARDS)

        _incrementTerm(self, self._wallets[0])
        _incrementTerm(self, self._wallets[0])

        tx_result = _distribute(self, self._wallets[0])

        self.assertEqual(tx_result["status"], True, "Distribute TX should succeed but did not!")
        _assertBalancesEqual(self, self._wallets[0].get_address(), self.MIN_VALUE_TO_GET_REWARDS, self.MIN_VALUE_TO_GET_REWARDS, 0)

        for i in range(10):
            previous_balance = _getBalance(self, self._wallets[0].get_address())
            previous_transferable = _getTransferable(self, self._wallets[0].get_address())
            _incrementTerm(self, self._wallets[0])

            tx_result = _distribute(self, self._wallets[0])

            self.assertEqual(tx_result["status"], True, "Distribute TX should succeed but did not!")
            self.assertGreater(_getBalance(self, self._wallets[0].get_address()), previous_balance, "Balance should be greater but is not!")
            self.assertGreater(_getTransferable(self, self._wallets[0].get_address()), previous_transferable, "Transferable should be greater but is not!")
            self.assertEqual(_getLocked(self, self._wallets[0].get_address()), 0, "Locked has the wrong value!")

        self.assertEqual(1, len(_getHolders(self)), "len(holders) should be 1 but is not!")

    def testDistributeFail(self):
        # Join one wallet to avoid "empty LinkedList" Error
        _join(self, self._wallets[0], self.MIN_VALUE_TO_GET_REWARDS)

        # Call distribute before the term that was set in SCORE's "on_install"
        tx_result = _distribute(self, self._wallets[0])
        self.assertEqual(tx_result['status'], False, "Distribute TX should fail but did not!")

        # Call one term later
        _incrementTerm(self, self._wallets[0])
        tx_result = _distribute(self, self._wallets[0])
        self.assertEqual(tx_result['status'], False, "Distribute TX should fail but did not!")

        # Call on correct term
        _incrementTerm(self, self._wallets[0])
        tx_result = _distribute(self, self._wallets[0])
        self.assertEqual(tx_result['status'], True, "Distribute TX should succeed but did not!")

        # Call again on same term
        tx_result = _distribute(self, self._wallets[0])
        self.assertEqual(tx_result['status'], False, "Distribute TX should fail but did not!")

    def testTransfer(self):
        _join(self, self._wallets[0], self.MIN_VALUE_TO_GET_REWARDS * 2)
        _incrementTerm(self, self._wallets[0])
        _incrementTerm(self, self._wallets[0])
        _distribute(self, self._wallets[0])
        _assertBalancesEqual(self, self._wallets[0].get_address(), self.MIN_VALUE_TO_GET_REWARDS * 2, self.MIN_VALUE_TO_GET_REWARDS * 2, 0)
        _assertBalancesEqual(self, self._wallets[1].get_address(), 0, 0, 0)

        # Transfer less than self.MIN_VALUE_TO_GET_REWARDS
        tx_result = _transfer(self, self._wallets[0], self._wallets[1].get_address(), 1000)

        self.assertEqual(tx_result["status"], True, "Transfer TX should succeed but did not!")
        _assertBalancesEqual(self, self._wallets[0].get_address(), self.MIN_VALUE_TO_GET_REWARDS * 2 - 1000, self.MIN_VALUE_TO_GET_REWARDS * 2 - 1000, 0)
        _assertBalancesEqual(self, self._wallets[1].get_address(), 1000, 1000, 0)
        holders = _getHolders(self)
        self.assertIn(self._wallets[0].get_address(), holders, "Wallet should be in holders but is not!")
        self.assertNotIn(self._wallets[1].get_address(), holders, "Wallet should not be in holders but is!")

        # Transfer a total of self.MIN_VALUE_TO_GET_REWARDS
        tx_result = _transfer(self, self._wallets[0], self._wallets[1].get_address(), self.MIN_VALUE_TO_GET_REWARDS - 1000)

        self.assertEqual(tx_result["status"], True, "Transfer TX should succeed but did not!")
        _assertBalancesEqual(self, self._wallets[0].get_address(), self.MIN_VALUE_TO_GET_REWARDS, self.MIN_VALUE_TO_GET_REWARDS, 0)
        _assertBalancesEqual(self, self._wallets[1].get_address(), self.MIN_VALUE_TO_GET_REWARDS, self.MIN_VALUE_TO_GET_REWARDS, 0)
        holders = _getHolders(self)
        print(holders)
        self.assertIn(self._wallets[0].get_address(), holders, "Wallet should be in holders but is not!")
        self.assertIn(self._wallets[1].get_address(), holders, "Wallet should be in holders but is not!")

        # Transfer a total of more than self.MIN_VALUE_TO_GET_REWARDS
        tx_result = _transfer(self, self._wallets[0], self._wallets[1].get_address(), 1000)

        self.assertEqual(tx_result["status"], True, "Transfer TX should succeed but did not!")
        _assertBalancesEqual(self, self._wallets[0].get_address(), self.MIN_VALUE_TO_GET_REWARDS - 1000, self.MIN_VALUE_TO_GET_REWARDS - 1000, 0)
        _assertBalancesEqual(self, self._wallets[1].get_address(), self.MIN_VALUE_TO_GET_REWARDS + 1000, self.MIN_VALUE_TO_GET_REWARDS + 1000, 0)
        holders = _getHolders(self)
        self.assertNotIn(self._wallets[0].get_address(), holders, "Wallet should not be in holders but is!")
        self.assertIn(self._wallets[1].get_address(), holders, "Wallet should be in holders but is not!")

        # Transfer all balance
        tx_result = _transfer(self, self._wallets[0], self._wallets[1].get_address(), self.MIN_VALUE_TO_GET_REWARDS - 1000)
        self.assertEqual(tx_result["status"], True, "Transfer TX should succeed but did not!")

        # Transfer 0 LICX
        tx_result = _transfer(self, self._wallets[0], self._wallets[1].get_address(), 0)
        self.assertEqual(tx_result["status"], True, "0 LICX Transfer TX should succeed but did not!")

        _assertBalancesEqual(self, self._wallets[0].get_address(), 0, 0, 0)
        _assertBalancesEqual(self, self._wallets[1].get_address(), self.MIN_VALUE_TO_GET_REWARDS * 2, self.MIN_VALUE_TO_GET_REWARDS * 2, 0)
        holders = _getHolders(self)
        self.assertNotIn(self._wallets[0].get_address(), holders, "Wallet should not be in holders but is!")
        self.assertIn(self._wallets[1].get_address(), holders, "Wallet should be in holders but is not!")

    def testTransferFail(self):
        # Transfer without joining
        tx_result = _transfer(self, self._wallets[0], self._wallets[1].get_address(), self.MIN_VALUE_TO_GET_REWARDS)
        self.assertEqual(tx_result["status"], False, "Transfer TX should fail but did not!")

        # Join and distribute so we have LICX to test with
        _join(self, self._wallets[0], self.MIN_VALUE_TO_GET_REWARDS)
        _incrementTerm(self, self._wallets[0])
        _incrementTerm(self, self._wallets[0])
        _distribute(self, self._wallets[0])
        _assertBalancesEqual(self, self._wallets[0].get_address(), self.MIN_VALUE_TO_GET_REWARDS, self.MIN_VALUE_TO_GET_REWARDS, 0)

        # Transfer more than balance
        tx_result = _transfer(self, self._wallets[0], self._wallets[1].get_address(), self.MIN_VALUE_TO_GET_REWARDS + 1)
        self.assertEqual(tx_result["status"], False, "Transfer TX should fail but did not!")

        # Transfer negative amount
        tx_result = _transfer(self, self._wallets[0], self._wallets[1].get_address(), -1)
        self.assertEqual(tx_result["status"], False, "Transfer TX should fail but did not!")

        # Transfer to zero address
        tx_result = _transfer(self, self._wallets[0], self._wallets[1].get_address(), ZERO_WALLET_ADDRESS)
        self.assertEqual(tx_result["status"], False, "Transfer TX should fail but did not!")

        # Ensure that balance stayed the same as before the failed calls
        _assertBalancesEqual(self, self._wallets[0].get_address(), self.MIN_VALUE_TO_GET_REWARDS, self.MIN_VALUE_TO_GET_REWARDS, 0)

    @unittest.skip("Always get this error: 'TokenFallbackInterface() takes no arguments'")
    def testTransferToSCORE(self):
        # Deploy a SCORE that implements tokenFallback()
        simple_test_score_address = _testDeploy(self, relative_score_path="simple_test_score/", _from=self._wallets[0])["scoreAddress"]

        # Join so that we have some balance
        _join(self, self._wallets[0], self.MIN_VALUE_TO_GET_REWARDS)
        _incrementTerm(self, self._wallets[0])
        _incrementTerm(self, self._wallets[0])
        _distribute(self, self._wallets[0])
        _assertBalancesEqual(self, self._wallets[0].get_address(), self.MIN_VALUE_TO_GET_REWARDS, self.MIN_VALUE_TO_GET_REWARDS, 0)

        # Transfer to SCORE that implements tokenFallback()
        tx_result = _transfer(self, self._wallets[0], simple_test_score_address, 1000)
        self.assertEqual(tx_result["status"], True, "Transfer TX should succeed but did not!")

        # Transfer to SCORE that does not implement tokenFallback()
        tx_result = _transfer(self, self._wallets[0], self._score_address_fake_system_score, 1000)
        self.assertEqual(tx_result["status"], False, "Transfer TX should fail but did not!")

        _assertBalancesEqual(self, self._wallets[0].get_address(), self.MIN_VALUE_TO_GET_REWARDS - 1000, self.MIN_VALUE_TO_GET_REWARDS - 1000, 0)

    def testSetIterationLimit(self):
        self.assertEqual(_getIterationLimit(self), 500, "Iteration Limit should be 500 but is not!")

        tx_result = _setIterationLimit(self, self._wallets[0], 1000)

        self.assertEqual(True, tx_result['status'], "setIterationLimit TX should succeed but did not!")
        self.assertEqual(_getIterationLimit(self), 1000, "Iteration Limit should be 1000 but is not!")

    def testSetIterationLimitFail(self):
        # Call with non owner
        tx_result = _setIterationLimit(self, self._wallets[1], 1000)
        self.assertEqual(False, tx_result['status'], "setIterationLimit TX should fail but did not!")

        # Call with negative iteration limit
        tx_result = _setIterationLimit(self, self._wallets[0], -1)
        self.assertEqual(False, tx_result['status'], "setIterationLimit TX should fail but did not!")

        # Call with 0 as iteration limit
        tx_result = _setIterationLimit(self, self._wallets[1], 0)
        self.assertEqual(False, tx_result['status'], "setIterationLimit TX should fail but did not!")

        self.assertEqual(_getIterationLimit(self), 500, "Iteration Limit should be 500 but is not!")


if __name__ == '__main__':
    unittest.main()
