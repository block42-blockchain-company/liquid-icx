import json
from pyllist import dllist
import random


def constrained_sum_sample_pos(n, total):
    """ For generating n random int's, which sum up to total """
    dividers = sorted(random.sample(range(1, total), n - 1))
    return [a - b for a, b in zip(dividers + [total], [0] + dividers)]


def writeToJsonFile(file_name: str, data: dict or list):
    with open(file_name, "w") as output:
        json.dump(data, output, indent=2)


def readFromJsonFile(file_name: str) -> dict:
    with open(file_name) as f:
        return json.load(f)


def findInList(dl_list: dllist, n_id: int):
    for node in dl_list.iternodes():
        if node.value[0] == n_id:
            return node


def distribute():
    """"
    Function simulates the LICX distribute function.
    It's using a json file (json-db.json) as a very simple DB, where the data is stored for in-between calls.
    """
    db = readFromJsonFile("json-db.json")
    address_list = dllist(readFromJsonFile("address-list.json"))
    balance_list = readFromJsonFile("balances-list.json")
    distributed_rewards = list()
    rewards_sum = 0

    if db["rewards"] == 0:
        # "claim rewards"
        db["rewards"] = int("0x187ae15a5fdc1f527", 16)  # around 28.22351972 ICX
        db["iterator"] = address_list.first.value[0]
        db["rewards_sum"] = 0

    it = 1
    cur = findInList(address_list, db["iterator"])
    while cur:
        try:
            cur_id = cur.value[0]
            cur_address = cur.value[1]
            cur = cur.next
            if True:
                # distribute
                distributed_rewards.append((balance_list[cur_id - 1] / db["total_supply"] * db["rewards"]))
                rewards_sum += (balance_list[cur_id - 1] / db["total_supply"] * db["rewards"])
            if cur_address == address_list.last.value[1]:
                # reset
                print(f"Claimed rewards: {db['rewards']}")
                db["rewards"] = 0
                db["iterator"] = 0
                db["rewards_sum"] += rewards_sum
                print(f"Distributed rewards: {db['rewards_sum']}")
            if it >= db["it-limit"]:
                # save iterator
                db["iterator"] = cur.value[0]
                db["rewards_sum"] += rewards_sum
                break
            it += 1
        except AttributeError as e:
            break

    writeToJsonFile("json-db.json", db)
    # writeToJsonFile("distributed-balances-list.json", distributed_rewards)


def reset():
    writeToJsonFile("json-db.json", {
        "it-limit": 50,
        "rewards": 0,
        "iterator": 0,
        "total_supply": 39599169400000000000000,
        "rewards_sum": 0
    })


if __name__ == "__main__":
    # reset() # Un-comment to reset the json-db and comment after the first call
    distribute()
