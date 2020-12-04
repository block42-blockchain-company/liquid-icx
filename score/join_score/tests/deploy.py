import os

from iconsdk.builder.transaction_builder import DeployTransactionBuilder
from iconsdk.icon_service import IconService
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from tbears.libs.icon_integrate_test import SCORE_INSTALL_ADDRESS

import pprint as pp


def deployJoinScore(wallet: KeyWallet, icon_service: IconService, proccess_tx_fn) -> dict:
    dir_path = os.path.abspath(os.path.dirname(__file__))
    score_project = os.path.abspath(os.path.join(dir_path, '..'))
    score_content_bytes = gen_deploy_data_content(score_project)

    # Generates an instance of transaction for deploying SCORE.
    transaction = DeployTransactionBuilder() \
        .from_(wallet.get_address()) \
        .to(SCORE_INSTALL_ADDRESS) \
        .nid(3) \
        .step_limit(10000000000) \
        .nonce(100) \
        .content_type("application/zip") \
        .content(score_content_bytes) \
        .params({}) \
        .build()

    # Returns the signed transaction object having a signature
    signed_transaction = SignedTransaction(transaction, wallet)

    # process the transaction in local
    tx_result = proccess_tx_fn(signed_transaction, icon_service)
    return tx_result


