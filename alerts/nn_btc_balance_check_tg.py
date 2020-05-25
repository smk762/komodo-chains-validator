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
BOT_CHAT_ID = os.getenv('BOT_CHAT_ID')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

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
    for notary in notary_pubkeys:
        pubkey = notary_pubkeys[notary]
        address = electrum_lib.get_addr_from_pubkey(pubkey)
        print(notary+" BTC: "+address)
        balance = electrum_lib.get_full_electrum_balance(pubkey,
                                 'electrum1.cipig.net', '10000')/100000000
        print(notary+" BTC: "+str(balance))
        address = "<a href='https://live.blockcypher.com/btc/address/" \
                   +address+"/'>"+address+"</a>"

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

    splitted_text = util.split_string(msg, 3000)

    for text in splitted_text:
        text = "<pre>"+text+"</pre>"
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, parse_mode=ParseMode.HTML)
        bot.send_message(chat_id=BOT_CHAT_ID, text=text, parse_mode=ParseMode.HTML)

# e.g. /get_balance BTC
@bot.message_handler(commands=['get_btc_balances'])
def get_balances(message):
    try:
        bot.reply_to(message, "Scanning electrums, will reply with balances in a bit...")
        get_btc_balances()
    except Exception as e:
        bot.reply_to(message, e)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text+ " is not a valid command. Try `/get_btc_balances`")

bot.polling() 
