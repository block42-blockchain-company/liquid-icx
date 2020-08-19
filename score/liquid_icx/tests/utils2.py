import os

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.builder.transaction_builder import DeployTransactionBuilder, CallTransactionBuilder, \
    TransactionBuilder
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from tbears.libs.icon_integrate_test import SCORE_INSTALL_ADDRESS


#################################################################################################################
# UTILS
#################################################################################################################

TERM_LENGTH = 43120


def _estimateSteps(self, margin) -> int:
    GOV_score_address = "cx0000000000000000000000000000000000000001"
    tx = _buildTransaction(self, type="read", method="getStepCosts",
                                _to=GOV_score_address, params={})
    result = self._icon_service.call(tx)
    return int(result["contractCall"], 16) + margin


def _buildTransaction(self, _to: str, type="write", **kwargs):
    if type not in ("transfer", "write", "read"):
        raise ValueError("Wrong method value")

    from_ = KeyWallet.create().get_address() if "from_" not in kwargs else kwargs["from_"]
    margin_ = 15000000 if "margin" not in kwargs else kwargs["margin"]
    value_ = 0 if "value" not in kwargs else kwargs["value"]
    method_ = None if "method" not in kwargs else kwargs["method"]
    params_ = {} if "params" not in kwargs else kwargs["params"]

    if type == "write":
        steps_ = _estimateSteps(self, margin_)
        tx = CallTransactionBuilder() \
            .from_(from_) \
            .to(_to) \
            .value(value_) \
            .nid(3) \
            .step_limit(steps_) \
            .nonce(100) \
            .method(method_) \
            .params(params_) \
            .build()
    elif type == "read":
        tx = CallBuilder() \
            .to(_to) \
            .method(method_) \
            .params(params_) \
            .build()
    elif type == "transfer":
        steps_ = _estimateSteps(self, margin_)
        tx = TransactionBuilder() \
            .from_(from_) \
            .to(_to) \
            .value(value_) \
            .step_limit(steps_) \
            .nid(3) \
            .build()

    return tx


def _testDeploy(self, relative_score_path: str, _from: KeyWallet, params: dict = {},
                deploy_address: str = SCORE_INSTALL_ADDRESS) -> dict:
    dir_path = os.path.abspath(os.path.dirname(__file__))
    score_project = os.path.abspath(os.path.join(dir_path, relative_score_path))
    score_content_bytes = gen_deploy_data_content(score_project)

    transaction = DeployTransactionBuilder() \
        .from_(_from.get_address()) \
        .to(deploy_address) \
        .nid(3) \
        .step_limit(10000000000) \
        .nonce(100) \
        .content_type("application/zip") \
        .content(score_content_bytes) \
        .params(params) \
        .build()

    signed_transaction = SignedTransaction(transaction, _from)

    tx_result = self.process_transaction(signed_transaction, self._icon_service)

    self.pp.pprint(tx_result)

    self.assertEqual(True, tx_result["status"], "Deploying the SCORE failed!")
    self.assertTrue('scoreAddress' in tx_result, "scoreAddress should be in deployment TX but is not!")

    return tx_result


def _getBalance(self, address: str) -> int:
    params = {"_owner": address}
    tx = _buildTransaction(self, _to=self._score_address_licx, type="read",
                           from_=self._wallets[0].get_address(), method="balanceOf", params=params)
    return int(self.process_call(tx, self._icon_service), 16)


def _getTransferable(self, address: str) -> int:
    params = {"_owner": address}
    tx = _buildTransaction(self, _to=self._score_address_licx, type="read",
                           from_=self._wallets[0].get_address(), method="transferableOf", params=params)
    return int(self.process_call(tx, self._icon_service), 16)


def _getLocked(self, address: str) -> int:
    params = {"_owner": address}
    tx = _buildTransaction(self, _to=self._score_address_licx, type="read",
                           from_=self._wallets[0].get_address(), method="lockedOf", params=params)
    return int(self.process_call(tx, self._icon_service), 16)


def _getIISSInfo(self) -> dict:
    tx = _buildTransaction(self, _to=self._score_address_fake_system_score, type="read",
                           from_=self._wallets[0].get_address(), method="getIISSInfo")
    return self.process_call(tx, self._icon_service)


def _getPRepTerm(self) -> dict:
    tx = _buildTransaction(self, _to=self._score_address_fake_system_score, type="read",
                           from_=self._wallets[0].get_address(), method="getPRepTerm")
    return self.process_call(tx, self._icon_service)


def _getHolders(self) -> list:
    tx = _buildTransaction(self, _to=self._score_address_licx, type="read",
                           from_=self._wallets[0].get_address(), method="getHolders")
    return self.process_call(tx, self._icon_service)


def _getIterationLimit(self) -> int:
    tx = _buildTransaction(self, _to=self._score_address_licx, type="read",
                           from_=self._wallets[0].get_address(), method="getIterationLimit")
    return int(self.process_call(tx, self._icon_service), 16)


def _incrementTerm(self, from_: KeyWallet) -> dict:
    tx = _buildTransaction(self, _to=self._score_address_fake_system_score, type="write",
                           from_=from_.get_address(), method="incrementTerm")
    signed_transaction = SignedTransaction(tx, from_)
    tx_result = self.process_transaction(signed_transaction, self._icon_service)
    self.pp.pprint(tx_result)
    return tx_result


def _join(self, from_: KeyWallet, value: int) -> dict:
    tx = _buildTransaction(self, _to=self._score_address_licx, type="write",
                                from_=from_.get_address(), method="join",
                                value=value)
    signed_transaction = SignedTransaction(tx, from_)
    tx_result = self.process_transaction(signed_transaction, self._icon_service)
    self.pp.pprint(tx_result)
    return tx_result


def _joinDontWaitForTxResult(self, from_: KeyWallet, value: int) -> None:
    tx = _buildTransaction(self, _to=self._score_address_licx, type="write",
                                from_=from_.get_address(), method="join",
                                value=value)
    signed_transaction = SignedTransaction(tx, from_)
    self._icon_service.send_transaction(signed_transaction)


def _distribute(self, from_: KeyWallet) -> dict:
    tx = _buildTransaction(self, _to=self._score_address_licx, type="write",
                           from_=from_.get_address(), method="distribute")
    signed_transaction = SignedTransaction(tx, from_)
    tx_result = self.process_transaction(signed_transaction, self._icon_service)
    self.pp.pprint(tx_result)
    return tx_result


def _transfer(self, from_: KeyWallet, _to: str, value: int) -> dict:
    params = {"_to": _to, "_value": str(value)}
    tx = _buildTransaction(self, _to=self._score_address_licx, type="write",
                           from_=from_.get_address(), method="transfer", params=params)
    signed_transaction = SignedTransaction(tx, from_)
    tx_result = self.process_transaction(signed_transaction, self._icon_service)
    self.pp.pprint(tx_result)
    return tx_result


def _setIterationLimit(self, from_: KeyWallet, iteration_limit: int) -> dict:
    params = {"_iteration_limit": iteration_limit}
    tx = _buildTransaction(self, _to=self._score_address_licx, type="write",
                           from_=from_.get_address(), method="setIterationLimit", params=params)
    signed_transaction = SignedTransaction(tx, from_)
    tx_result = self.process_transaction(signed_transaction, self._icon_service)
    self.pp.pprint(tx_result)
    return tx_result


def _assertBalancesEqual(self, address: str, expected_balance: int, expected_transferable: int, expected_locked: int) -> None:
    self.assertEqual(_getBalance(self, address), expected_balance,
                     "Balance has the wrong value!")
    self.assertEqual(_getTransferable(self, address), expected_transferable,
                     "Transferable has the wrong value!")
    self.assertEqual(_getLocked(self, address), expected_locked,
                     "Locked has the wrong value!")
