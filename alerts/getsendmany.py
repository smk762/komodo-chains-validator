#!/usr/bin/env python3
import os
import json

with open(os.path.dirname(os.path.abspath(__file__))+'/balances_report.json') as j:
    balance_data = json.load(j)
balance_thresholds = {
    "BTC": 0.03,
    "AYA": 1,
    "EMC2": 1,
    "GAME": 1,
    "OTHER": 0.05,
}

for chain in balance_data["low_balance_chains"]:
    sendmany = {}
    if chain in balance_thresholds:
        val = balance_thresholds[chain]
    else:
        val = balance_thresholds["OTHER"]
    for notary in balance_data["low_balance_notaries"]:
        if chain in balance_data["low_balances"][notary]:
            sendmany.update({balance_data["low_balances"][notary][chain]["address"]:val})
    try:
        print(chain+': sendmany "" "'+json.dumps(sendmany).replace('"', '\\"')+'"')
    except:
        pass
