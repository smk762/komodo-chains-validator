#!/usr/bin/env python3
import requests
import os
import json
import time
from logging import Handler, Formatter
import logging
import datetime
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

s4_nn = {
        "alien_AR": "03911a60395801082194b6834244fa78a3c30ff3e888667498e157b4aa80b0a65f",
        "alien_EU": "03bb749e337b9074465fa28e757b5aa92cb1f0fea1a39589bca91a602834d443cd",
        "strob_NA": "02a1c0bd40b294f06d3e44a52d1b2746c260c475c725e9351f1312e49e01c9a405",
        "titomane_SH": "020014ad4eedf6b1aeb0ad3b101a58d0a2fc570719e46530fd98d4e585f63eb4ae",
        "fullmoon_AR": "03b251095e747f759505ec745a4bbff9a768b8dce1f65137300b7c21efec01a07a",
        "phba2061_EU": "03a9492d2a1601d0d98cfe94d8adf9689d1bb0e600088127a4f6ca937761fb1c66",
        "fullmoon_NA": "03931c1d654a99658998ce0ddae108d825943a821d1cddd85e948ac1d483f68fb6",
        "fullmoon_SH": "03c2a1ed9ddb7bb8344328946017b9d8d1357b898957dd6aaa8c190ae26740b9ff",
        "madmax_AR": "022be5a2829fa0291f9a51ff7aeceef702eef581f2611887c195e29da49092e6de",
        "titomane_EU": "0285cf1fdba761daf6f1f611c32d319cd58214972ef822793008b69dde239443dd",
        "cipi_NA": "022c6825a24792cc3b010b1531521eba9b5e2662d640ed700fd96167df37e75239",
        "indenodes_SH": "0334e6e1ec8285c4b85bd6dae67e17d67d1f20e7328efad17ce6fd24ae97cdd65e",
        "decker_AR": "03ffdf1a116300a78729608d9930742cd349f11a9d64fcc336b8f18592dd9c91bc",
        "indenodes_EU": "0221387ff95c44cb52b86552e3ec118a3c311ca65b75bf807c6c07eaeb1be8303c",
        "madmax_NA": "02997b7ab21b86bbea558ae79acc35d62c9cedf441578f78112f986d72e8eece08",
        "chainzilla_SH": "02288ba6dc57936b59d60345e397d62f5d7e7d975f34ed5c2f2e23288325661563",
        "peer2cloud_AR": "0250e7e43a3535731b051d1bcc7dc88fbb5163c3fe41c5dee72bd973bcc4dca9f2",
        "pirate_EU": "0231c0f50a06655c3d2edf8d7e722d290195d49c78d50de7786b9d196e8820c848",
        "webworker01_NA": "02dfd5f3cef1142879a7250752feb91ddd722c497fb98c7377c0fcc5ccc201bd55",
        "zatjum_SH": "036066fd638b10e555597623e97e032b28b4d1fa5a13c2b0c80c420dbddad236c2",
        "titomane_AR": "0268203a4c80047edcd66385c22e764ea5fb8bc42edae389a438156e7dca9a8251",
        "chmex_EU": "025b7209ba37df8d9695a23ea706ea2594863ab09055ca6bf485855937f3321d1d",
        "indenodes_NA": "02698c6f1c9e43b66e82dbb163e8df0e5a2f62f3a7a882ca387d82f86e0b3fa988",
        "patchkez_SH": "02cabd6c5fc0b5476c7a01e9d7b907e9f0a051d7f4f731959955d3f6b18ee9a242",
        "metaphilibert_AR": "02adad675fae12b25fdd0f57250b0caf7f795c43f346153a31fe3e72e7db1d6ac6",
        "etszombi_EU": "0341adbf238f33a33cc895633db996c3ad01275313ac6641e046a3db0b27f1c880",
        "pirate_NA": "02207f27a13625a0b8caef6a7bb9de613ff16e4a5f232da8d7c235c7c5bad72ffe",
        "metaphilibert_SH": "0284af1a5ef01503e6316a2ca4abf8423a794e9fc17ac6846f042b6f4adedc3309",
        "indenodes_AR": "02ec0fa5a40f47fd4a38ea5c89e375ad0b6ddf4807c99733c9c3dc15fb978ee147",
        "chainmakers_NA": "029415a1609c33dfe4a1016877ba35f9265d25d737649f307048efe96e76512877",
        "mihailo_EU": "037f9563f30c609b19fd435a19b8bde7d6db703012ba1aba72e9f42a87366d1941",
        "tonyl_AR": "0299684d7291abf90975fa493bf53212cf1456c374aa36f83cc94daece89350ae9",
        "alien_NA": "03bea1ac333b95c8669ec091907ea8713cae26f74b9e886e13593400e21c4d30a8",
        "pungocloud_SH": "025b97d8c23effaca6fa7efacce20bf54df73081b63004a0fe22f3f98fece5669f",
        "node9_EU": "029ffa793b5c3248f8ea3da47fa3cf1810dada5af032ecd0e37bab5b92dd63b34e",
        "smdmitry_AR": "022a2a45979a6631a25e4c96469423de720a2f4c849548957c35a35c91041ee7ac",
        "nodeone_NA": "03f9dd0484e81174fd50775cb9099691c7d140ff00c0f088847e38dc87da67eb9b",
        "gcharang_SH": "02ec4172eab854a0d8cd32bc691c83e93975a3df5a4a453a866736c56e025dc359",
        "cipi_EU": "02f2b6defff1c544202f66e47cfd6909c54d67c7c39b9c2a99f137dbaf6d0bd8fa",
        "etszombi_AR": "0329944b0ac65b6760787ede042a2fde0be9fca1d80dd756bc0ee0b98d389b7682",
        "pbca26_NA": "0387e0fb6f2ca951154c87e16c6cbf93a69862bb165c1a96bcd8722b3af24fe533",
        "mylo_SH": "03b58f57822e90fe105e6efb63fd8666033ea503d6cc165b1e479bbd8c2ba033e8",
        "swisscertifiers_EU": "03ebcc71b42d88994b8b2134bcde6cb269bd7e71a9dd7616371d9294ec1c1902c5",
        "marmarachain_AR": "035bbd81a098172592fe97f50a0ce13cbbf80e55cc7862eccdbd7310fab8a90c4c",
        "karasugoi_NA": "0262cf2559703464151153c12e00c4b67a969e39b330301fdcaa6667d7eb02c57d",
        "phm87_SH": "021773a38db1bc3ede7f28142f901a161c7b7737875edbb40082a201c55dcf0add",
        "oszy_EU": "03d1ffd680491b98a3ec5541715681d1a45293c8efb1722c32392a1d792622596a",
        "chmex_AR": "036c856ea778ea105b93c0be187004d4e51161eda32888aa307b8f72d490884005",
        "dragonhound_NA": "0227e5cad3731e381df157de189527aac8eb50d82a13ce2bd81153984ebc749515",
        "strob_SH": "025ceac4256cef83ca4b110f837a71d70a5a977ecfdf807335e00bc78b560d451a",
        "madmax_EU": "02ea0cf4d6d151d0528b07efa79cc7403d77cb9195e2e6c8374f5074b9a787e287",
        "dudezmobi_AR": "027ecd974ff2a27a37ee69956cd2e6bb31a608116206f3e31ef186823420182450",
        "daemonfox_NA": "022d6f4885f53cbd668ad7d03d4f8e830c233f74e3a918da1ed247edfc71820b3d",
        "nutellalicka_SH": "02f4b1e71bc865a79c05fe333952b97cb040d8925d13e83925e170188b3011269b",
        "starfleet_EU": "025c7275bd750936862b47793f1f0bb3cbed60fb75a48e7da016e557925fe375eb",
        "mrlynch_AR": "031987dc82b087cd53e23df5480e265a5928e9243e0e11849fa12359739d8b18a4",
        "greer_NA": "03e0995615d7d3cf1107effa6bdb1133e0876cf1768e923aa533a4e2ee675ec383",
        "mcrypt_SH": "025faab3cc2e83bf7dad6a9463cbff86c08800e937942126f258cf219bc2320043",
        "decker_EU": "03777777caebce56e17ca3aae4e16374335b156f1dd62ee3c7f8799c6b885f5560",
        "dappvader_SH": "02962e2e5af746632016bc7b24d444f7c90141a5f42ce54e361b302cf455d90e6a",
        "alright_DEV": "02b73a589d61691efa2ada15c006d27bc18493fea867ce6c14db3d3d28751f8ce3",
        "artemii235_DEV": "03bb616b12430bdd0483653de18733597a4fd416623c7065c0e21fe9d96460add1",
        "tonyl_DEV": "02d5f7fd6e25d34ab2f3318d60cdb89ff3a812ec5d0212c4c113bb12d12616cfdc",
        "decker_DEV": "028eea44a09674dda00d88ffd199a09c9b75ba9782382cc8f1e97c0fd565fe5707"
    }

season = "Season_3"
chain = 'BTC'
balances_api = 'http://notary.earth:8762/api/source/balances/?chain='+chain+'&node=main&season='+season
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
