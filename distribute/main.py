import json
import os
from time import sleep

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import CallTransactionBuilder
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from tbears.libs.icon_integrate_test import SCORE_INSTALL_ADDRESS

import requests as rq
from requests.exceptions import HTTPError
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


def getBlockHeight() -> int:
    return icx_service.get_block("latest")["height"]


def getLastDistributeEventHeight() -> int:
    tracker_endpoint = os.getenv("TRACKER_API") + "/eventLogList"
    params = {"page": 1, "count": 1000, "contractAddr": score_addr}
    response = rq.get(tracker_endpoint, params=params)
    if response.status_code == 200:
        for log in response.json()["data"]:
            found = log["eventLog"].find("Distribute")
            if found > 0:
                return log["height"]
    else:
        response.raise_for_status()


def distribute():
    pass


def main():
    global icx_service
    global score_addr
    icx_service = IconService(HTTPProvider(os.getenv("PROVIDER")))
    score_addr = os.getenv("SCORE")

    while True:
        try:
            term_bounds = getCurrentTermBounds()
            last_distribute_height = getLastDistributeEventHeight()
            blocks_left = term_bounds["end"] - getBlockHeight()
            if term_bounds["start"] > last_distribute_height and blocks_left < 1000:
                distribute()
            else:
                sleep(5)
        except HTTPError as e:
            print(e)


if __name__ == "__main__":
    main()
