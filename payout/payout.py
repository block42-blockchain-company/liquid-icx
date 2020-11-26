import sys, os, json
from pathlib import Path

import requests as rq
import pprint as pp
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider

icon_service = IconService(HTTPProvider("https://ctz.solidwallet.io/api/v3"))
tracker_url = "https://tracker.icon.foundation/v3/"
licx_address = "cxb799844c58d5e5afb08ad4078566a78bd82d932c"


def getTxList(addr: str, page: int, count=100):
    if count > 100:
        count = 100

    txlist_endpoint = "contract/txList"
    paras_txlist = {
        "addr": addr,
        "page": page,
        "count": count
    }
    response = rq.get(tracker_url + txlist_endpoint, params=paras_txlist)
    response.raise_for_status()
    return response.json()


def getTxDetail(txhash):
    return icon_service.get_transaction(txhash)


def getEventLog(txhash):
    eventlog_endpoint = "transaction/eventLogList"
    paras_eventlog = {
        "txHash": txhash,
        "page": 1,
        "count": 100
    }
    response = rq.get(tracker_url + eventlog_endpoint, params=paras_eventlog)
    response.raise_for_status()
    return response.json()


def fetchEventLogs():
    """
    Fetching licx transactions that have event log and saves them into a json file
    """
    event_logs = dict()
    for page in range(1, 20):
        try:
            print(f"Page: {page}")
            tx_list = getTxList(licx_address, page)
            if tx_list is None:
                continue
            for tx in tx_list["data"]:
                txEventLog = getEventLog(tx["txHash"])
                if txEventLog["data"]:
                    for log in txEventLog["data"]:
                        event_logs[log["txHash"]] = log
        except Exception as e:
            pp.pprint(e)

    with open('eventLogs.json', 'w') as outfile:
        json.dump(event_logs, outfile, indent=4)


def parseEventLog(log: str):
    try:
        parsed = dict()
        splitted = log.split(",")
        for it in range(len(splitted)):
            if "LeaveRequest" in splitted[it]:
                parsed["LeaveRequest"] = {
                    "from": splitted[it + 2].strip(),
                    "value": int(splitted[it + 3].strip()[:-1],16)
                }
            elif "Join" in splitted[it]:
                parsed["Join"] = {
                    "from": splitted[it + 2].strip(),
                    "value": int(splitted[it + 3].strip()[:-1],16)
                }
            elif "ICXTransfer" in splitted[it]:
                parsed["ICXTransfer"] = {
                    "from": splitted[it + 3].strip(),
                    "to": splitted[it + 4].strip(),
                    "value": int(splitted[it + 5].strip()[:-1])
                }
            elif "Transfer" in splitted[it]:
                parsed["Transfer"] = {
                    "from": splitted[it + 4].strip(),
                    "to": splitted[it + 5].strip(),
                    "value": int(splitted[it + 6].strip()[:-1], 16)
                }
            elif "IScoreClaimedV2" in splitted[it]:
                parsed["IScoreClaimedV2"] = {
                    "address": splitted[it + 3].strip()[:-1],
                    "iscore": int(splitted[it + 4].strip(), 16),
                    "icx": int(splitted[it + 5].strip()[:-1], 16)
                }
    except Exception as e:
        pass

    return parsed


def main():
    balances = dict()

    event_logs_file = Path("eventLogs.json")
    if not event_logs_file.exists():
        fetchEventLogs()

    with open("eventLogs.json", 'r', encoding='raw_unicode_escape') as f:
        event_logs: dict = json.load(f)
        for log in event_logs.values():
            parsed_eventlog = parseEventLog(log["eventLog"])
            if "Join" in parsed_eventlog:
                if parsed_eventlog["Join"]["from"] in balances:
                    balances[parsed_eventlog["Join"]["from"]] += parsed_eventlog["Join"]["value"]
                else:
                    balances[parsed_eventlog["Join"]["from"]] = parsed_eventlog["Join"]["value"]
            elif "ICXTransfer" in parsed_eventlog:
                if parsed_eventlog["ICXTransfer"]["to"] in balances:
                    balances[parsed_eventlog["ICXTransfer"]["to"]] -= parsed_eventlog["ICXTransfer"]["value"]
                else:
                    balances[parsed_eventlog["ICXTransfer"]["to"]] = parsed_eventlog["ICXTransfer"]["value"]
            elif "Transfer" in parsed_eventlog:
                # Decremeant from address
                if parsed_eventlog["Transfer"]["from"] in balances:
                    balances[parsed_eventlog["Transfer"]["from"]] -= parsed_eventlog["Transfer"]["value"]
                else:
                    balances[parsed_eventlog["Transfer"]["from"]] = parsed_eventlog["Transfer"]["value"]
                # Increament to address
                if parsed_eventlog["Transfer"]["to"] in balances:
                    balances[parsed_eventlog["Transfer"]["to"]] += parsed_eventlog["Transfer"]["value"]
                else:
                    balances[parsed_eventlog["Transfer"]["to"]] = parsed_eventlog["Transfer"]["value"]

    sum = 0
    for balance in balances.values():
        sum += balance
    print(sum / 10 ** 18)
    pp.pprint(balances)


if __name__ == "__main__":
    main()
