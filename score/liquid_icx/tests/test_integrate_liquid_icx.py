import json
import logging
import os, sys
import pprint
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

DIR_PATH = os.path.abspath(os.path.dirname(__file__))


class LiquidICXTest(IconIntegrateTestBase):
    SCORE_PROJECT = os.path.abspath(os.path.join(DIR_PATH, '..'))

    FORCE_DEPLOY = False  # Change to True, if you want to deploy a new SCORE for testing
    LOCAL_NETWORK_TEST = False
    TEST_WITH_FAKE_SYS_SCORE = False

    SYS_SCORE_ADDRESS = "cx0000000000000000000000000000000000000000"
    GOV_SCORE_ADDRESS = "cx0000000000000000000000000000000000000001"

    LOCAL_TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"
    LOCAL_SCORE_ADDRESS = "cx77c06488a0b5567e881585d9336953bad22193ea"

    FAKE_SYS_SCORE_YEOUIDO = "cx2b01010a92bf78ee464be0b5eff94676e95cd757"

    YEUOIDO_TEST_HTTP_ENDPOINT_URI_V3 = "https://bicon.net.solidwallet.io/api/v3"
    # YEUOIDO_SCORE_ADDRESS = "cxfc51501665c72c26cb01ae009bbd1eddf0c79e4b"
    # YEUOIDO_SCORE_ADDRESS = "cx3b51da5f05f389859efae83b1d3c1672055985b1"
    # YEUOIDO_SCORE_ADDRESS = "cx03619f2689cd214b198f8ecf9d4ef79e8a2025f3"
    YEUOIDO_SCORE_ADDRESS = "cx03619f2689cd214b198f8ecf9d4ef79e8a2025f3"
    # YEUOIDO_SCORE_ADDRESS = "cx81e6776779ea846da7f8762c6faf091a72e13786"

    pp = pprint.PrettyPrinter(indent=4)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if LiquidICXTest.TEST_WITH_FAKE_SYS_SCORE:
            cls.replace_in_consts_py(LiquidICXTest.SYS_SCORE_ADDRESS, LiquidICXTest.FAKE_SYS_SCORE_YEOUIDO)

        if LiquidICXTest.LOCAL_NETWORK_TEST:
            cls._wallet = KeyWallet.load("../../keystore_test1", "test1_Account")
            cls._icon_service = IconService(HTTPProvider(LiquidICXTest.LOCAL_TEST_HTTP_ENDPOINT_URI_V3))
            cls._score_address = LiquidICXTest.LOCAL_SCORE_ADDRESS
        else:
            cls._wallet = KeyWallet.load("../../keystore_test3", "test3_Account")
            cls._wallet2 = KeyWallet.load("../../keystore_test1", "test1_Account")
            cls._icon_service = IconService(HTTPProvider(LiquidICXTest.YEUOIDO_TEST_HTTP_ENDPOINT_URI_V3))
            cls._score_address = LiquidICXTest.YEUOIDO_SCORE_ADDRESS

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        if LiquidICXTest.TEST_WITH_FAKE_SYS_SCORE:
            cls.replace_in_consts_py(LiquidICXTest.FAKE_SYS_SCORE_YEOUIDO, LiquidICXTest.SYS_SCORE_ADDRESS)

    @classmethod
    def replace_in_consts_py(cls, pattern, sub):
        for line in fileinput.input("../consts.py", inplace=1):
            if "SYSTEM_SCORE" in line:
                line = line.replace(pattern, sub)
            print(line, end='')

    def setUp(self, **kwargs):
        super().setUp()

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

    def test_get_next_prep_term_IISS(self):
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
        LiquidICXTest.pp.pprint(result)
        # return result['nextPRepTerm']

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

    def test_100_join(self):
        result = []
        with ThreadPoolExecutor(max_workers=100) as pool:
            for it in range(0, 100):
                tx_res = pool.submit(self._join_with_new_wallet)
                result.append(tx_res)
        self.assertEqual(100, len(self.test_get_holders()))

    def test_join_with_new_wallet(self):
        self._join_with_new_wallet()

    def test_get_holders(self):
        tx = self._build_transaction(method="getHolders", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)
        # self.assertEqual(True, tx_result["status"], msg=LiquidICXTest.pp.pformat(tx_result))
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

    def test_get_staked(self):
        tx = self._build_transaction(method="getStaked", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)

    def test_get_delegation(self):
        tx = self._build_transaction(method="getDelegation", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)

    def test_unlock_holder_licx(self):
        tx = self._build_transaction(method="unlockHolderLicx", type_="write", margin=5000000)
        tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)

    def test_get_arrays_count(self):
        tx = self._build_transaction(method="test", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)

    def test_test(self):
        paras = {"address": "hx0a6d9812218e4507f4224d38dc60450960e7a4ff"}
        tx = self._build_transaction(method="selectFromHolders", type_="read", params=paras)
        tx_result = self.process_call(tx, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)

    def test_test_123(self):
        paras = {"id": "69"}
        tx = self._build_transaction(method="getDelegation", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)

    def test_queryIscore(self):
        tx = self._build_transaction(method="queryIScore", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)

    def test_distribute(self):
        tx = self._build_transaction(method="distribute", margin=500000)
        tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)

    def _test_query_iscore(self):
        paras = {
            "address": self._wallet.get_address()
        }
        tx = self._build_transaction(method="queryIScore", type_="read",
                                     params=paras, margin=500000, to=SCORE_INSTALL_ADDRESS)
        tx_result = self.process_call(tx, self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)
        """
        Before Claim:
            {   
            'blockHeight': '0x4da417',
            'estimatedICX': '0x391eb87d8a56f3c06',
            'iscore': '0xdf2000aa6463a827a93'
            }
        After Claim:
        {   
            'blockHeight': '0x4da417', 
            'estimatedICX': '0x0', 
            'iscore': '0x323'
        }
        """

    def _test_claim_iscore(self):
        tx = self._build_transaction(method="claimIScore", margin=500000, to=SCORE_INSTALL_ADDRESS)
        tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
        LiquidICXTest.pp.pprint(tx_result)
        """
        Tx result: 
        {   
            'blockHash': '0x15177bd242be43636ba53cad9d3a159cfcbdb7165c3c01cd4fb5c4a050bdbfd6',
            'blockHeight': 5161046,
            'cumulativeStepUsed': 104800,
            'eventLogs': [   {   'data': [   '0xdf2000aa6463a827770',
                                             '0x391eb87d8a56f3c06'],
                                 'indexed': [   'IScoreClaimedV2(Address,int,int)',
                                                'hx16668be6daa4bfa22af768270d51aec9d37fa227'],
                                 'scoreAddress': 'cx0000000000000000000000000000000000000000'}],
            'logsBloom':.....
            'status': 1,
            'stepPrice': 10000000000,
            'stepUsed': 104800,
            'to': 'cx0000000000000000000000000000000000000000',
            'txHash': '0xc3c502f0568b49bb4fc7a46f1c2cf7dbacc38f33e488fe0b6eda362db43c220e',
            'txIndex': 1
        }    
        """


