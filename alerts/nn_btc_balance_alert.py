#!/usr/bin/env python3
import os
import json
import time
import logging
import telebot
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

def get_btc_balances():

    now = int(time.time())

    if now > seasons['Season_3']['end_time']:
        pubkey_file = 's4_nn_pubkeys.json'
    else:
        pubkey_file = 's3_nn_pubkeys.json'

    pubkey_file = os.path.join(os.path.dirname(__file__), pubkey_file)

    with open(pubkey_file) as f:
        notary_pubkeys = json.load(f)

    msg = ''
    i = 1
    for notary in notary_pubkeys:
        print("scanning "+str(i)+" / "+str(len(notary_pubkeys))+" NN addresses...")
        pubkey = notary_pubkeys[notary]
        address = electrum_lib.get_addr_from_pubkey(pubkey)
        address = "<a href='https://live.blockcypher.com/btc/address/" \
                   +address+"/'>"+address+"</a>"
        print(notary+" BTC: "+address)
        balance = electrum_lib.get_full_electrum_balance(pubkey,
                                 'electrum1.cipig.net', '10000')/100000000
        print(notary+" BTC: "+str(balance))

        print("{} has {} BALANCE {} for {}\n" \
                    .format("["+address+"]", 'BTC',
                            "["+str(balance)+"]", "["+notary+"]"))

        if float(balance) < 0.01:
            msg += "{} has LOW {} BALANCE {} for {}\n" \
                    .format("["+address+"]", 'BTC',
                            "["+str(balance)+"]", "["+notary+"]")
            print(msg)

        else:
            # msg += "As at {}, {} {} balance OK {} for {}\n" \
            #        .format(str(update_time), "["+address+"]", chain, "["+balance+"]", "["+notary+"]",)
            pass
        time.sleep(0.2)
        i += 1

    logger.error(msg)

get_btc_balances()
