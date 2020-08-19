import json
from time import sleep

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import CallTransactionBuilder
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from tbears.libs.icon_integrate_test import SCORE_INSTALL_ADDRESS

import requests as rq
import pprint as pp

TEST_NET = "https://bicon.net.solidwallet.io/api/v3"
MAIN_NET = "https://ctz.solidwallet.io"

score_addr = "cx054ad2db4d2c39646b975629e8190e65a674e80f"

events_endpoint = "https://bicon.tracker.solidwallet.io/v3/contract/eventLogList?page=1&count=1000&contractAddr="

icx_service = IconService(HTTPProvider(TEST_NET))


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
    event_list = rq.get(events_endpoint + score_addr).json()["data"]
    for log in event_list:
        found = log["eventLog"].find("Distribute")
        if found > 0:
            return log["height"]


def distribute():
    pass


def main():
    while True:
        term_bounds = getCurrentTermBounds()
        last_distribute_height = getLastDistributeEventHeight()
        blocks_left = term_bounds["end"] - getBlockHeight()
        if term_bounds["start"] > last_distribute_height and blocks_left < 1000:
            distribute()
            pass
        else:
            print("zzz")
            sleep(5)


if __name__ == "__main__":
    main()
