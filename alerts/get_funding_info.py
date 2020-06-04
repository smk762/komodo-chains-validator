#!/usr/bin/env python3
import os
import json
import time
import logging
import datetime
import requests
import rpc_lib
from datetime import datetime as dt
from rpc_lib import rpc, dpow_tickers

import electrum_lib
from dotenv import load_dotenv
from logging import Handler, Formatter

load_dotenv()

BB_PK = os.getenv("BB_PK")
BB_ADDR = os.getenv("BB_ADDR")
 
logger = logging.getLogger()

seasons = {
    "Season_3": {
            "start_time":1563148800,
            "end_time":1592146799
    },
    "Season_4": {
            "start_time":1592146800,
            "end_time":1751328000
    }
}

now = int(time.time())

def get_season(time_stamp):
    for season in seasons:
        if time_stamp >= seasons[season]['start_time'] and time_stamp <= seasons[season]['end_time']:
            return season
    return "season_undefined"

if now > seasons['Season_3']['end_time']:
    season = "Season_4"
    pubkey_file = 's4_nn_pubkeys.json'
    pubkey_file_3p = 's4_nn_pubkeys_3p.json'
else:
    season = "Season_3"
    pubkey_file = 's3_nn_pubkeys.json'
    pubkey_file_3p = 's3_nn_pubkeys_3p.json'

pubkey_file = os.path.join(os.path.dirname(__file__), pubkey_file)
with open(pubkey_file) as f:
    notary_pubkeys = json.load(f)

pubkey_file_3p = os.path.join(os.path.dirname(__file__), pubkey_file_3p)
with open(pubkey_file_3p) as f:
    notary_pubkeys_3p = json.load(f)

notaries = list(notary_pubkeys.keys())
notaries.sort()


human_now = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime())
time.ctime(now)

# Check outgoing transactions from balance bot address
funding_tx = []
bot_balances = {}
for chain in dpow_tickers:
    try:
        block_ht = rpc[chain].getblockcount()
        balance = rpc[chain].getbalance()
        bot_balances.update({chain:balance})

        address_txids = rpc[chain].listtransactions("*",9999,0)
        print("Scanning "+chain+" txids fom funding address...")
        print(str(len(address_txids))+" returned.")


        for item in address_txids:
            #print(item)
            txid = item['txid']
            if 'blocktime' in item:
                tx_block_time = item['blocktime']
            else:
                tx_block_time = now
            tx_category = item['category']
            if tx_category == "send":
                tx_fee = item['fee']
            else:
                tx_fee = 0
            if 'blockhash' in item:
                tx_block_hash = item['blockhash']
            else:
                tx_block_hash = 'unconfirmed'
            tx_amount = item['amount']
            if tx_block_hash == 'unconfirmed':
                tx_block_height = 0
            else:
                tx_block_height = rpc[chain].getblock(tx_block_hash)['height']
            funding_tx.append({
                "chain":chain,
                "txid":txid,
                "vout":item['vout'],
                "address":item['address'],
                "block_time":tx_block_time,
                "fee":tx_fee,
                "block_hash":tx_block_hash,
                "amount":tx_amount,
                "category":tx_category,
                "block_height":tx_block_height,
                "season":get_season(tx_block_time)
            })
    except Exception as e:
        print(chain+" delta calc failed: "+ str(e))

with open(os.path.dirname(os.path.abspath(__file__))+'/funding_tx.json', 'w+') as j:
    json.dump(funding_tx, j, indent = 4, sort_keys=True)

with open(os.path.dirname(os.path.abspath(__file__))+'/notary_funds.json', 'w+') as j:
    json.dump(bot_balances, j, indent = 4, sort_keys=True)



funding_totals = {"fees":{}}
now = int(time.time())
for item in funding_tx:
    if item["address"] not in ["unknown", "funding bot"]:
        if item["address"] not in funding_totals:
            funding_totals.update({item["address"]:{}})

        if item["chain"] not in funding_totals[item["address"]]:
            funding_totals[item["address"]].update({item["chain"]:-item["amount"]})
        else:
            val = funding_totals[item["address"]][item["chain"]]-item["amount"]
            funding_totals[item["address"]].update({item["chain"]:val})

        if item["chain"] not in funding_totals["fees"]:
            funding_totals["fees"].update({item["chain"]:-item["fee"]})
        else:
            val = funding_totals["fees"][item["chain"]]-item["fee"]
            funding_totals["fees"].update({item["chain"]:val})

with open(os.path.dirname(os.path.abspath(__file__))+'/funding_totals.json', 'w+') as j:
    json.dump(funding_totals, j, indent = 4, sort_keys=True)

