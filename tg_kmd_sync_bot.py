import requests
import os
import time
from logging import Handler, Formatter
import logging
import datetime
from dotenv import load_dotenv

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

logger.setLevel(logging.WARNING)

while True:
    r = requests.get('http://138.201.207.24/show_hashtips')
    if r.status_code == 200:
        hashtips = r.json()
        msg = ''
        for ticker in hashtips:
            if ticker == 'last_updated':
                pass
            else:
                block = list(hashtips[ticker].keys())[0]
                if len(hashtips[ticker][block]) > 1:
                    # potentially forked!
                    for blockhash in hashtips[ticker][block]:
                        nodes = hashtips[ticker][block][blockhash]        
                        msg += "{} FORK!\nBlock {}\nHash {}\n".format("["+ticker+"]", "["+block+"]", "["+blockhash+"]")
                        msg += '-------------------------------------------\n'
                    pass
                else:
                    blockhash = list(hashtips[ticker][block].keys())[0]
                    nodes = hashtips[ticker][block][blockhash]
                    msg += "{} OK!\nBlock {}\nHash {}\n".format("["+ticker+"]", "["+block+"]", "["+blockhash+"]")
                    msg += '-------------------------------------------\n'
            if len(msg) > 3000:
                logger.error(msg)
                msg = ''
    else:
        msg = "`Bot's not here man... (API not responding).`"
    logger.error(msg)
    print(msg)
    time.sleep(300)
