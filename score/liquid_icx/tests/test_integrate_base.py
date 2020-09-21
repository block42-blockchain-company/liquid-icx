import unittest
import os
import pprint as pp
from concurrent.futures.thread import ThreadPoolExecutor

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import CallTransactionBuilder, TransactionBuilder, DeployTransactionBuilder
from iconsdk.icon_service import IconService
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS
from dotenv import load_dotenv


class LICXTestBase(IconIntegrateTestBase):
    _wallet: KeyWallet
    LOCAL_NETWORK_TEST = False

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_dotenv()

        if not cls.LOCAL_NETWORK_TEST:
            cls._wallet = KeyWallet.load("../../keystore_test3", "test3_Account")
            cls._wallet2 = KeyWallet.load("../../keystore_test2", "test2_Account")
            cls._icon_service = IconService(HTTPProvider(os.getenv("YEUOIDO_NET_URL")))
            cls._score_address = os.getenv("YEUOIDO_SCORE_ADDRESS")
            cls._fake_sys_score = os.getenv("YEUOIDO_FAKE_SYS_SCORE")
        else:
            cls._wallet = KeyWallet.load("../../keystore_test1", "test1_Account")
            cls._icon_service = IconService(HTTPProvider(os.getenv("LOCAL_NET_URL")))
            cls._score_address = os.getenv("LOCAL_SCORE_ADDRESS")

    # -----------------------------------------------------------------------
    # ----------------------- testing helper methods ------------------------
    # -----------------------------------------------------------------------

    def _deploy_score(self, to: str = SCORE_INSTALL_ADDRESS) -> dict:
        dir_path = os.path.abspath(os.path.dirname(__file__))
        score_project = os.path.abspath(os.path.join(dir_path, '..'))
        score_content_bytes = gen_deploy_data_content(score_project)

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

        self.assertEqual(True, tx_result['status'], msg=pp.pformat(tx_result))
        self.assertTrue('scoreAddress' in tx_result, msg=pp.pformat(tx_result))

        return tx_result

    def _build_transaction(self, type_="write", **kwargs):
        if type_ not in ("transfer", "write", "read"):
            raise ValueError("Wrong type value")

        from_ = self._wallet.get_address() if "from_" not in kwargs else kwargs["from_"]
        to_ = self._score_address if "to" not in kwargs else kwargs["to"]
        margin_ = 2500000 if "margin" not in kwargs else kwargs["margin"]
        value_ = 0 if "value" not in kwargs else kwargs["value"]
        method_ = None if "method" not in kwargs else kwargs["method"]
        params_ = {} if "params" not in kwargs else kwargs["params"]

        tx = None
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

    def _estimate_steps(self, margin) -> int:
        tx = self._build_transaction(type_="read",
                                     method="getStepCosts",
                                     to=os.getenv("GOV_SCORE_ADDRESS"),
                                     params={})
        result = self._icon_service.call(tx)
        return int(result["contractCall"], 16) + margin

    def _transfer_icx_from_to(self, from_: KeyWallet, to: any, value: int, condition: bool = True):
        to = to if isinstance(to, str) else to.get_address()
        tx = self._build_transaction(type_="transfer",
                                     from_=from_.get_address(),
                                     to=to,
                                     value=value * 10 ** 18)
        tx_result = self.process_transaction(SignedTransaction(tx, from_), self._icon_service)
        self.assertEqual(tx_result["status"], condition, msg=pp.pformat(tx_result))
        return tx_result

    def _join_with_new_created_wallet(self) -> KeyWallet:
        # create a wallet and transfer 11 ICX to it
        wallet = KeyWallet.create()
        tx = self._build_transaction(type_="transfer", to=wallet.get_address(), value=11 * 10 ** 18)
        tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
        self.assertEqual(True, tx_result["status"], msg=pp.pformat(tx_result))
        # make a join request
        tx = self._build_transaction(method="join", from_=wallet.get_address(), params={}, value=10 * 10 ** 18)
        tx_result = self.process_transaction(SignedTransaction(tx, wallet), self._icon_service)
        self.assertEqual(True, tx_result["status"], msg=pp.pformat(tx_result))
        return wallet

    def _n_join(self, n: int = 10, workers: int = 10) -> list:
        result = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for it in range(0, n):
                future = pool.submit(self._join_with_new_created_wallet)
                result.append(future)
        return result

    def _n_leave(self, wallet_list: list, workers: int = 10):
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for wallet in wallet_list:
                _balance = int(self._balance_of(wallet.result().get_address()), 16)
                pool.submit(self._leave,
                            wallet.result(),
                            int(_balance * 10 ** -18))

    def _n_claim(self, wallet_list: list, workers: int = 10):
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for wallet in wallet_list:
                pool.submit(self._claim, wallet.result())

    def _n_transfer_icx(self, wallet_list: list, to: KeyWallet = None, workers: int = 10):
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for wallet in wallet_list:
                pool.submit(self._transfer_icx_from_to, wallet, to, 9)


    # -----------------------------------------------------------------------
    # ---------------------------- LICX methods -----------------------------
    # -----------------------------------------------------------------------
    def _join(self, from_: KeyWallet = None, value: int = None):
        wallet = from_ if from_ is not None else self._wallet
        value = value if value is not None else 10
        tx = self._build_transaction(method="join", value=value * 10 ** 18, from_=wallet.get_address())
        tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
        return tx_result

    def _distribute(self):
        tx = self._build_transaction(method="distribute", margin=100000000000)
        tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
        # LiquidICXTest.pp.pprint(tx_result)
        return tx_result

    def _leave(self, from_: KeyWallet = None, value: int = None, condition: bool = True):
        if from_ is None:
            from_ = self._wallet
        paras = {
            "_value": value * 10 ** 18 if value is not None else value
        }
        tx = self._build_transaction(method="leave",
                                     from_=from_.get_address(),
                                     params=paras)
        signed_transaction = SignedTransaction(tx, from_)
        tx_result = self.process_transaction(signed_transaction, self._icon_service)
        self.assertEqual(tx_result["status"], condition)
        return tx_result

    def _claim(self,  from_: KeyWallet = None, condition: bool = True):
        if from_ is None:
            from_ = self._wallet
        tx = self._build_transaction(method="claim", from_=from_.get_address())
        tx_result = self.process_transaction(SignedTransaction(tx, from_), self._icon_service)
        self.assertEqual(tx_result["status"], condition, msg=pp.pformat(tx_result))
        # LiquidICXTest.pp.pprint(tx_result)
        return tx_result

    def _get_wallets(self):
        tx = self._build_transaction(method="getWallets", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        # pp.pprint(tx_result)
        return tx_result

    def _get_wallet(self, address=None):
        address = self._wallet.get_address() if address is None else address
        paras = {
            "_address": address
        }
        tx = self._build_transaction(method="getWallet", type_="read", params=paras)
        tx_result = self.process_call(tx, self._icon_service)
        # pp.pprint(tx_result)
        return tx_result

    def _get_staked(self):
        tx = self._build_transaction(method="getStaked", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        # pp.pprint(tx_result)
        return tx_result

    def _get_delegation(self):
        tx = self._build_transaction(method="getDelegation", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        # pp.pprint(tx_result)
        return tx_result

    def _get_iteration_limit(self):
        tx = self._build_transaction(method="getIterationLimit", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        # pp.pprint(tx_result)
        return tx_result

    def _get_rewards(self):
        tx = self._build_transaction(method="rewards", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        # pp.pprint(tx_result)

    def _set_iteration_limit(self, limit: int = 500):
        paras = {
            "_iteration_limit": limit
        }
        tx = self._build_transaction(method="setIterationLimit", params=paras)
        tx_result = self.process_transaction(SignedTransaction(tx, self._wallet), self._icon_service)
        self.assertTrue(tx_result["status"], msg=tx_result)
        return tx_result



    # -----------------------------------------------------------------------
    # ---------------------------- IRC2 methods -----------------------------
    # -----------------------------------------------------------------------

    def _balance_of(self, address=None):
        address = self._wallet.get_address() if address is None else address
        paras = {"_owner": address}
        tx = self._build_transaction(method="balanceOf", params=paras, type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        # pp.pprint(tx_result)
        return tx_result

    def _total_supply(self):
        tx = self._build_transaction(method="totalSupply", type_="read")
        tx_result = self.process_call(tx, self._icon_service)
        # pp.pprint(tx_result)
        return tx_result

    def _transfer_licx_from_to(self, from_: KeyWallet = None, to: str = None, value: int = None):
        from_ = self._wallet if from_ is None else from_
        to = self._wallet2.get_address() if to is None else to
        value = value if value is not None else 1
        paras = {
            "_to": to,
            "_value": value * 10 ** 18
        }
        tx = self._build_transaction(method="transfer", params=paras, from_=from_.get_address())
        tx_result = self.process_transaction(SignedTransaction(tx, from_), self._icon_service)
        # pp.pprint(tx_result)
        return tx_result
