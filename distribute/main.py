import os
from time import sleep

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import CallTransactionBuilder
from iconsdk.exception import JSONRPCException
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from tbears.libs.icon_integrate_test import SCORE_INSTALL_ADDRESS

import requests as rq
import pprint as pp

# globals
icx_service: IconService
score_addr: str


def getCurrentTermBounds() -> dict:
    """
    :return: Term start/end-block height
    """
    call = CallBuilder() \
        .to(SCORE_INSTALL_ADDRESS) \
        .method("getPRepTerm") \
        .build()
    prep_term = icx_service.call(call)
    return {
        "start": int(prep_term["startBlockHeight"], 16),
        "end": int(prep_term["endBlockHeight"], 16)
    }


def getTXResult(tx_hash) -> dict:
    while True:
        try:
            return icx_service.get_transaction_result(tx_hash)
        except JSONRPCException as e:
            if e.args[0]["message"] == "Pending transaction":
                sleep(1)


def getLastDistributeEventHeight() -> int:
    tracker_endpoint = os.getenv("TRACKER_API") + "contract/eventLogList"
    params = {"page": 1, "count": 1000, "contractAddr": score_addr}
    response = rq.get(tracker_endpoint, params=params)
    if response.status_code == 200:
        for log in response.json()["data"]:
            found = log["eventLog"].find("Distribute")
            if found > 0:
                return log["height"]
    else:
        response.raise_for_status()

def getCreatedSCOREHeight() -> int:
    tracker_endpoint = os.getenv("TRACKER_API") + "contract/info"
    params = {"addr": score_addr}
    response = rq.get(tracker_endpoint, params=params)
    if response.status_code == 200:
        create_tx = response.json()["data"]["createTx"]
        tracker_endpoint = os.getenv("TRACKER_API") + "transaction/txDetail"
        params = {"txHash": create_tx}
        response = rq.get(tracker_endpoint, params=params)
        if response.status_code == 200:
            return response.json()["data"]["height"]
        else:
            response.raise_for_status()
    else:
        response.raise_for_status()

def distribute():
    wallet = KeyWallet.load(bytes.fromhex(os.getenv("PRIVATE_KEY")))
    tx = CallTransactionBuilder() \
        .from_(wallet.get_address()) \
        .to(score_addr) \
        .value(0) \
        .nid(3) \
        .step_limit(500000000) \
        .nonce(100) \
        .method("distribute") \
        .params({}) \
        .build()
    tx = SignedTransaction(tx, wallet)
    tx_res = getTXResult(icx_service.send_transaction(tx))
    pp.pprint(tx_res)


def main():
    global icx_service
    global score_addr
    icx_service = IconService(HTTPProvider(os.getenv("PROVIDER")))
    score_addr = os.getenv("SCORE")
    while True:
        try:
            term_bounds = getCurrentTermBounds()
            last_distribute_height = getLastDistributeEventHeight()
            score_created = getCreatedSCOREHeight()
            if score_created + (43120 * 2) < term_bounds["start"] and \
               (last_distribute_height is None or term_bounds["start"] > last_distribute_height):
                distribute()
                sleep(2)  # sleep so tracker has already the last distribute tx
            else:
                sleep(5)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
