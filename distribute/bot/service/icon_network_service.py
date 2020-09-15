import requests
from iconsdk.builder.transaction_builder import CallTransactionBuilder

from iconsdk.exception import JSONRPCException
from iconsdk.signed_transaction import SignedTransaction
from tbears.libs.icon_integrate_test import SCORE_INSTALL_ADDRESS
from iconsdk.builder.call_builder import CallBuilder
from time import sleep
from constants import *


def getCurrentTermBounds() -> dict:
    """
    :return: Term start/end-block height
    """

    call = CallBuilder() \
        .to(SCORE_INSTALL_ADDRESS) \
        .method("getPRepTerm") \
        .build()
    prep_term = ICX_SERVICE.call(call)
    return {
        "start": int(prep_term["startBlockHeight"], 16),
        "end": int(prep_term["endBlockHeight"], 16)
    }


def getTXResult(tx_hash) -> dict:
    while True:
        try:
            return ICX_SERVICE.get_transaction_result(tx_hash)
        except JSONRPCException as e:
            if e.args[0]["message"] == "Pending transaction":
                sleep(1)


def getLastDistributeEventHeight() -> int:
    params = {"page": 1, "count": 1000, "contractAddr": SCORE_ADDRESS}
    contract_addr_response = requests.get(TRACKER_ENDPOINT, params=params)

    if contract_addr_response.status_code != 200:
        raise BadStatusException(contract_addr_response)

    for log in contract_addr_response.json()["data"]:
        found = log["eventLog"].find("Distribute")
        if found > 0:
            return log["height"]

    return 0


def getCreateTX() -> str:
    while True:
        params = {"addr": SCORE_ADDRESS}
        addr_response = requests.get(TRACKER_ENDPOINT, params=params)
        if addr_response.status_code == 200:
            return addr_response.json()["data"]["createTx"]


def getCreatedSCOREHeight(create_tx) -> int:
    while True:
        params = {"txHash": create_tx}
        tx_hash_response = requests.get(TRACKER_ENDPOINT, params=params)
        if tx_hash_response.status_code == 200:
            return tx_hash_response.json()["data"]["height"]


def distribute():
    tx = CallTransactionBuilder() \
        .from_(WALLET.get_address()) \
        .to(SCORE_ADDRESS) \
        .value(0) \
        .nid(3) \
        .step_limit(500000000) \
        .nonce(100) \
        .method("distribute") \
        .params({}) \
        .build()
    tx = SignedTransaction(tx, WALLET)
    tx_res = getTXResult(ICX_SERVICE.send_transaction(tx))
    logger.info(tx_res)


class BadStatusException(Exception):
    def __init__(self, response: requests.Response):
        self.message = "Error while network request.\nReceived status code: " + \
                       str(response.status_code) + '\nReceived response: ' + response.text
