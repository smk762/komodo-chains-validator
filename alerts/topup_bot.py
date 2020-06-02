#!/usr/bin/env python3
import os
import time
import json
import rpc_lib
import datetime
from datetime import datetime as dt
from rpc_lib import rpc, dpow_tickers
from dotenv import load_dotenv

load_dotenv()

BB_PK = os.getenv("BB_PK")
BB_ADDR = os.getenv("BB_ADDR")


with open('balances_report.json', 'r') as j:
    balance_data = json.load(j)

bot_balances = {}
for notary in balance_data['low_balances']:
    for chain in balance_data['low_balances'][notary]:
        balance = balance_data['low_balances'][notary][chain]['balance']
        address = balance_data['low_balances'][notary][chain]['address']

        if chain != 'BTC':
            print("["+notary+"] ["+chain+"] ["+str(balance)+"] ["+address+"]")

            # import privkey in case chain restarted, then send
            try:
                rpc[chain].importprivkey(BB_PK)
                txid = rpc[chain].sendtoaddress(address, 0.001)
                while txid not in rpc[chain].getrawmempool():
                    time.sleep(1)
            except Exception as e:
                print("ERR: "+str(e))

# Check outgoing transactions from balance bot address
bot_balances = {}
balance_deltas = {}
for chain in dpow_tickers:
    txid_balance_deltas = {}
    try:
        block_ht = rpc[chain].getblockcount()
        balance = rpc[chain].getbalance()
        bot_balances.update({chain:balance})

        address_txids = rpc[chain].getaddresstxids({"addresses": [BB_ADDR], "start":0, "end":block_ht})

        for txid in address_txids:
            print(txid)
            txid_balance_deltas = rpc_lib.get_balance_bot_data(chain, txid)

        for ticker in txid_balance_deltas:
            if ticker not in balance_deltas:
                balance_deltas.update({ticker:txid_balance_deltas[ticker]})
            else:
                val = txid_balance_deltas[ticker] + balance_deltas[ticker]
                balance_deltas.update({ticker:val})

    except Exception as e:
        print(chain+" failed: "+ str(e))

with open(os.path.dirname(os.path.abspath(__file__))+'/balances_deltas.json', 'w+') as j:
    json.dump(balance_deltas, j, indent = 4, sort_keys=True)

with open(os.path.dirname(os.path.abspath(__file__))+'/notary_funds.json', 'w+') as j:
    json.dump(bot_balances, j, indent = 4, sort_keys=True)

