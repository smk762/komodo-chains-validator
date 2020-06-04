

#!/usr/bin/env python3
import os
import json
import time
import logging
import telebot
import datetime
import threading
import concurrent.futures
from telebot import util
from telegram import ParseMode
import requests
import rpc_lib
from datetime import datetime as dt
from rpc_lib import rpc, dpow_tickers

import electrum_lib
from dotenv import load_dotenv
from logging import Handler, Formatter

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
BB_PK = os.getenv("BB_PK")
BB_ADDR = os.getenv("BB_ADDR")


class RequestsHandler(Handler):
    def emit(self, record):
        log_entry = self.format(record)
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': log_entry,
            'parse_mode': 'HTML'
        }
        return requests.post("https://api.telegram.org/bot{token}/sendMessage".format(token=TELEGRAM_TOKEN),
                             data=payload).content

class LogstashFormatter(Formatter):
    def __init__(self):
        super(LogstashFormatter, self).__init__()

    def format(self, record):
        t = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        return "<i>{datetime}</i><pre>\n{message}</pre>".format(message=record.msg, datetime=t)

logger = logging.getLogger()
logger.setLevel(logging.WARNING)




handler = RequestsHandler()
formatter = LogstashFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)

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

with open(os.path.dirname(os.path.abspath(__file__))+'/funding_totals.json', 'r') as j:
    funding_totals = json.load(j)

with open(os.path.dirname(os.path.abspath(__file__))+'/funding_tx.json', 'r') as j:
    funding_data = json.load(j)


with open(os.path.dirname(os.path.abspath(__file__))+'/balances_report.json', 'r') as j:
    balance_data = json.load(j)

funding_limit = 1
top_up_amount = 0.05
# make bot payments 
bot_balances = {}
for notary in balance_data['low_balances']:
    for chain in balance_data['low_balances'][notary]:
        balance = balance_data['low_balances'][notary][chain]['balance']
        address = balance_data['low_balances'][notary][chain]['address']
        if chain != 'BTC':
            if address in funding_totals:
                if chain in funding_totals[address]:
                    if funding_totals[address][chain] > funding_limit:
                        print("skipping "+notary+" top up for "+chain+", fund limit exceeded. "+str(balance)+" remains")
                    else:
                         # import privkey in case chain restarted, then send
                        try:
                            rpc[chain].importprivkey(BB_PK)
                            txid = rpc[chain].sendtoaddress(address, top_up_amount)
                            print("Top up for "+chain+" sent to "+notary)
                            print("TXID: "+txid)
                            while txid not in rpc[chain].getrawmempool():
                                time.sleep(1)
                        except Exception as e:
                            print("TOP UP ERR: "+str(e))




