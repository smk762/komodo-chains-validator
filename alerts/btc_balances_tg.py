import requests
import os
import json
import time
from logging import Handler, Formatter
import logging
import datetime
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BTC_BALANCE_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_BTC_BALANCE_CHAT_ID')

season = "Season_3"
chain = 'BTC'
balances_api = 'http://notary.earth:8762/source/balances/?chain='+chain+'&node=main&season='+season
ignore_notaries = ['dwy_EU','dwy_SH']

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

logger.setLevel(logging.WARNING)


while True:
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
                if len(msg) > 3000:
                    logger.error(msg)
                    print(msg)
                    msg = ''

    else:
        msg = "`Bot's not here man... (API not responding).`"
    logger.error(msg)
    print(msg)
    time.sleep(3600)
