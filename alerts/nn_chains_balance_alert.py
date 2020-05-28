#!/usr/bin/env python3
import os
import json
import time
import logging
import telebot
import threading
import concurrent.futures
from telebot import util
from telegram import ParseMode
import requests
import datetime
import electrum_lib
from dotenv import load_dotenv
from logging import Handler, Formatter

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

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
    pubkey_file = 's4_nn_pubkeys.json'
    pubkey_file_3p = 's4_nn_pubkeys_3p.json'
else:
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

class electrum_thread(threading.Thread):
    def __init__(self, chain, addr, pubkey, notary):
        threading.Thread.__init__(self)
        self.pubkey = pubkey
        self.chain = chain
        self.addr = addr
        self.notary = notary
    def run(self):
        thread_electrum(self.chain, 
                        self.addr, self.pubkey, self.notary)

def thread_electrum(chain, addr, pubkey, notary):
    balance_data = electrum_lib.get_balance(chain, addr, pubkey)
    if chain == 'KMD' and pubkey == notary_pubkeys_3p[notary]:
        chain = "KMD_3P"
    if chain not in balances_dict[notary]:
        balances_dict[notary].update({chain:{}})
    balances_dict[notary][chain].update({
                                    "address":addr,
                                    "balance":balance_data[0],
                                    "source":balance_data[1]
                                })

thread_list = {}
balances_dict = {}
def scan_balances():
    global balances_dict
    for notary in notaries:
        thread_list.update({notary:[]})
        balances_dict.update({notary:{}})
        scan_msg = ''

        for chain in electrum_lib.main_coins:
            pubkey = notary_pubkeys[notary]
            addr = electrum_lib.get_addr_from_pubkey(pubkey, chain)

            thread_list[notary].append(electrum_thread(chain, addr, pubkey, notary))

        for chain in electrum_lib.third_party_coins:
            pubkey = notary_pubkeys_3p[notary]
            addr = electrum_lib.get_addr_from_pubkey(pubkey, chain)
            
            thread_list[notary].append(electrum_thread(chain, addr, pubkey, notary))

        for thread in thread_list[notary]:
            thread.start()

        time.sleep(1)

scan_balances()

while len(balances_dict) < 64:
    print("Waiting for balances dict to populate..."+str(len(balances_dict)-1)+"/64 complete....")
    time.sleep(3)

num_coins = len(electrum_lib.main_coins) + len(electrum_lib.third_party_coins)

for notary in notaries:
    while len(balances_dict[notary]) < num_coins:
        print("Waiting for balances dict to populate..."+str(len(balances_dict)-1)+"/64 complete....")
        time.sleep(3)

print("Complete!")

from_dexstats = []
from_cipig = []
other_sources = {}
chain_fails = {}
low_balances = {}
for notary in notaries:
    for chain in balances_dict[notary]:
        if chain not in chain_fails:
            chain_fails.update({chain:[]})

        balance = balances_dict[notary][chain]["balance"]
        address = balances_dict[notary][chain]["address"]
        source = balances_dict[notary][chain]["source"]

        if source == "dexstats":
            from_dexstats.append(chain)
        elif source.find('cipig') != -1:
            from_cipig.append(chain)
        else:
            other_sources.update({chain: source})

        if balance == -1:
            chain_fails[chain].append(notary)
        elif float(balance) < 0.01:
            if notary not in low_balances:
                low_balances.update({notary:{}})
            low_balances[notary].update({
                    chain:{
                        "balance":balance,
                        "address":address
                    }
                })
messages = ''
for notary in low_balances:
    messages += "\n"
    messages += '******* '+'{:^40}'.format(notary+" has low balances!")+" *******\n"
    chains = list(low_balances[notary].keys())
    chains.sort()
    for chain in low_balances[notary]:
        address = low_balances[notary][chain]["address"]
        balance = low_balances[notary][chain]["balance"]
        messages +=  '{:^10}'.format(chain)+" "+address+" | "+str(balance)+"\n"
        if len(messages) > 3900:
            print(len(messages))
            logger.warning(messages)
            messages = ''

for chain in chain_fails:
    num_fails = len(chain_fails[chain])
    if num_fails > 0:
        messages += '{:^56}'.format(str(num_fails)+" failed balance queries for "+chain)+"\n"
        if len(messages) > 3900:
            print(len(messages))
            logger.warning(messages)
            messages = ''

if messages != '':
    logger.warning(messages+"\n")

print("From DexStats: "+str(set(from_dexstats)))
print("From Cipig: "+str(set(from_cipig)))
print("From Other: "+str(other_sources))
