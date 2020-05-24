import os
import json
import time
import logging
import telebot
from telebot import util
from telegram import ParseMode
import requests
import datetime
from dotenv import load_dotenv
from logging import Handler, Formatter

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
BOT_CHAT_ID = os.getenv('BOT_CHAT_ID')
bot = telebot.TeleBot(TELEGRAM_TOKEN)
ignore_notaries = ['dwy_EU','dwy_SH']
season = "Season_3"
print(TELEGRAM_CHAT_ID)

def get_chain_balances(chain):
    balances_api = 'http://notary.earth:8762/api/source/balances/?chain='+chain+'&node=main&season='+season
    r = requests.get(balances_api)
    if r.status_code == 200:
        balances = r.json()['results']
        msg = ''
        for result in balances:
            notary = result['notary']
            if notary not in ignore_notaries:
                balance = result['balance']
                address = result['address']
                update_time = time.ctime(result['update_time'])
                if float(result['balance']) < 0.01:
                    msg += "As at {}, {} has LOW {} BALANCE {} for {}\n" \
                            .format(str(update_time), "["+address+"]", chain, "["+balance+"]", "["+notary+"]",)
                else:
                    # msg += "As at {}, {} {} balance OK {} for {}\n" \
                    #        .format(str(update_time), "["+address+"]", chain, "["+balance+"]", "["+notary+"]",)
                    pass
    else:
        msg = "Bot's not here man... (API not responding)."
    splitted_text = util.split_string(msg, 3000)
    for text in splitted_text:
        text = "<pre>"+text+"</pre>"
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, parse_mode=ParseMode.HTML)
        bot.send_message(chat_id=BOT_CHAT_ID, text=text, parse_mode=ParseMode.HTML)

# e.g. /get_balance BTC
@bot.message_handler(commands=['get_btc_balances'])
def send_welcome(message):
    try:
        chain = "BTC"
        get_chain_balances(chain)
    except Exception as e:
        print(e)
        bot.reply_to(message, "Need to enter a coin! Try `/get_btc_balances`")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text+ " is not a valid command. Try `/get_btc_balances`")

bot.polling() 
