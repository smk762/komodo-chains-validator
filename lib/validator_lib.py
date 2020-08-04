from slickrpc import Proxy
import time
import subprocess
import platform
import requests
import os
import re
import sys
import json
import math
import shutil
import logging

from dotenv import load_dotenv
load_dotenv()

print("Getting BB envars...")
BB_PK = os.getenv("BB_PK")
BB_PUB = os.getenv("BB_PUB")

main_server_only = False

logger = logging.getLogger(__name__)

r = requests.get('http://notary.earth:8762/api/info/coins/?dpow_active=1')

dpow_coins_info = r.json()['results'][0]
dpow_tickers = []
for ticker in dpow_coins_info:
    if main_server_only:
        if dpow_coins_info[ticker]['dpow']['server'].lower() == 'dpow-mainnet':
            dpow_tickers.append(ticker)
    else:
        dpow_tickers.append(ticker)

# not enough space for btc on this server
if 'BTC' in dpow_tickers:
    dpow_tickers.remove('BTC')
logger.info("dpow_tickers: "+str(dpow_tickers))

# create app folders
app_subfolders = ['chains_status', 'ticker_output', 'config']

for folder in app_subfolders:
    if not os.path.exists(sys.path[0]+"/"+folder):
        os.makedirs(sys.path[0]+"/"+folder)

def colorize(string, color):
    colors = {
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'yellow': '\033[93m',
        'magenta': '\033[95m',
        'green': '\033[92m',
        'red': '\033[91m',
        'black': '\033[30m',
        'grey': '\033[90m',
        'pink': '\033[95m'
    }
    if color not in colors:
        return string
    else:
        return colors[color] + str(string) + '\033[0m'

def get_dexstats_balance(chain, addr):
    url = 'http://'+chain.lower()+'.explorer.dexstats.info/insight-api-komodo/addr/'+addr
    r = requests.get(url)
    balance = r.json()['balance']
    return balance

def get_dexstats_blockhash(chain, block_ht):
    url = 'http://'+chain.lower()+'.explorer.dexstats.info/insight-api-komodo/block-index/'+str(block_ht)
    r = requests.get(url)
    hash = r.json()['blockHash']
    return hash

def get_dexstats_sync(chain):
    url = 'http://'+chain.lower()+'.explorer.dexstats.info/insight-api-komodo/sync'
    r = requests.get(url)
    return r.json()

def def_credentials(chain):
    rpcport = '';
    operating_system = platform.system()
    if operating_system == 'Darwin':
        ac_dir = os.environ['HOME'] + '/Library/Application Support/Komodo'
    elif operating_system == 'Linux':
        ac_dir = os.environ['HOME'] + '/.komodo'
    elif operating_system == 'Windows':
        ac_dir = '%s/komodo/' % os.environ['APPDATA']
    if chain in dpow_tickers:
        if 'conf_path' in dpow_coins_info[chain]['dpow']:
            coin_config_file = str(dpow_coins_info[chain]['dpow']['conf_path'].replace("~",os.environ['HOME']))
        else:
            logger.warning("Conf path not in dpow info for "+chain)
            coin_config_file = str(ac_dir + '/' + chain + '/' + chain + '.conf')

    elif chain == 'KMD':
        coin_config_file = str(ac_dir + '/komodo.conf')
    else:
        coin_config_file = str(ac_dir + '/' + chain + '/' + chain + '.conf')
    if not os.path.isfile(coin_config_file):
        print(coin_config_file)
        conf_filepath = dpow_coins_info[ticker]['dpow']['conf_path']
        path_file = os.path.split(os.path.abspath(conf_filepath))
        conf_file = path_file[1]
        if os.path.isfile(os.environ['HOME']+'/komodo-chains-validator/confs/'+conf_file):
            shutil.copyfile(os.environ['HOME']+'/komodo-chains-validator/confs/'+conf_file, coin_config_file)
    if os.path.isfile(coin_config_file):
        with open(coin_config_file, 'r') as f:
            for line in f:
                l = line.rstrip()
                if re.search('rpcuser', l):
                    rpcuser = l.replace('rpcuser=', '')
                elif re.search('rpcpassword', l):
                    rpcpassword = l.replace('rpcpassword=', '')
                elif re.search('rpcport', l):
                    rpcport = l.replace('rpcport=', '')
        if len(rpcport) == 0:
            if chain == 'KMD':
                rpcport = 7771
            else:
                print("rpcport not in conf file, exiting")
                print("check " + coin_config_file)
                exit(1)
        logger.info("RPC set for "+chain)
        return (Proxy("http://%s:%s@127.0.0.1:%d" % (rpcuser, rpcpassword, int(rpcport))))
    else:
        errmsg = coin_config_file+" does not exist! Please confirm "+str(chain)+" daemon is installed"
        print(colorize(errmsg, 'red'))
        exit(1)

rpc = {}
for ticker in dpow_tickers:
    try:
        rpc[ticker] = def_credentials(ticker)
    except:
        print("RPC proxy for "+ticker+" failed")

kmd_dir = os.environ['HOME'] + '/.komodo'

# sync chains
def sim_chains_start_and_sync():
    # start with creating a proxy for each assetchain
    for ticker in dpow_tickers:
        # 60 sec wait during restart for getting rpc credentials
        # 60 sec * approx. 40 chains = 40 min to start
        restart_ticker(ticker)
    while True:
        dpow_getsync()
        # loop again in 15 min
        time.sleep(900)
    return True

# Clean ticker data folder
def clean_chain_data(ticker):
    stop_result = rpc[ticker].stop()
    logger.info(ticker + " stopped!")
    time.sleep(30)

    conf_filepath = dpow_coins_info[ticker]['dpow']['conf_path']
    path_file = os.path.split(conf_filepath)
    conf_path = path_file[0].replace("~",os.environ['HOME'])
    conf_file = path_file[1]

    # not removing confs or wallets
    if os.path.exists(conf_path+"/blocks"):
        shutil.rmtree(conf_path+"/blocks")

    if os.path.exists(conf_path+"/database"):
        shutil.rmtree(conf_path+"/database")
    if os.path.exists(conf_path+"/chainstate"):
        shutil.rmtree(conf_path+"/chainstate")
    if os.path.exists(conf_path+"/notarisations"):
        shutil.rmtree(conf_path+"/notarisations")

    logger.info(conf_path+" subfolders deleted")
    # some 3P chains do not create a conf, will need to do this manually by copying ./confs/{chain}.conf into required folder.
    if os.path.isfile(os.environ['HOME']+'/komodo-chains-validator/confs/'+conf_file):
        shutil.copyfile(os.environ['HOME']+'/komodo-chains-validator/confs/'+conf_file, conf_filepath)

def restart_ticker(ticker):
    try:
        rpc[ticker] = def_credentials(ticker)
        rpc[ticker].getinfo()
        restart = False
    except Exception as e:
        print(ticker+" not running")
        print(e)
        restart = True
    if restart:
        try:
            logger.info("restarting "+ticker)
            ticker_launch = dpow_coins_info[ticker]['dpow']['launch_params'] \
                            .replace("~",os.environ['HOME']).split(' ')
            # launch with pubkey so balance bot unspent returns to correct address.
            ticker_launch.append("-pubkey="+BB_PUB)
            ticker_output = open(sys.path[0]+'/ticker_output/'+ticker+"_output.log",'w+')
            subprocess.Popen(ticker_launch, stdout=ticker_output, stderr=ticker_output, universal_newlines=True)
            logger.info("sleeping 60 sec")
            time.sleep(60)
            # set RPC proxy and import PK
            logger.info("Setting RPC for "+ticker)
            rpc[ticker] = def_credentials(ticker)
            rpc[ticker].importprivkey(BB_PK)
        except Exception as e:
            logger.debug("error restarting ticker "+ticker+": "+str(e))

def get_sync_node_data():
    # Get sync node's latest hashes
    sync_data = {}
    if os.path.exists('/var/www/html/global_sync.json'):
        with open('/var/www/html/global_sync.json', 'r') as fp:
            sync_data = json.loads(fp.read())
    else:
        print('/var/www/html/global_sync.json')
        print("global_sync.json not found!")
    return sync_data

def dpow_getinfo():
    non_responsive = []
    for ticker in dpow_tickers:
        try:
            rpc[ticker] = def_credentials(ticker)
            print(rpc[ticker].getinfo())
        except:
            print(ticker+" not responding!")
            non_responsive.append(ticker)
    print("Non-responsive: "+str(non_responsive))

def get_explorer_blockhash(ticker, block):
    pass

def get_electrum_blockhash(ticker, block):
    pass


def dpow_getsync():
    non_responsive = []
    sync_data = get_sync_node_data()
    now = int(time.time())
    sync_data.update({"last_updated":now})
    sync_data.update({"last_updated_time":time.ctime(now)})

    for ticker in dpow_tickers:
        if ticker not in sync_data:
            sync_data.update({ticker:{}})
        try:
            rpc[ticker] = def_credentials(ticker)
            info = rpc[ticker].getinfo()
            sync_data[ticker].update({
                "blocks":info["blocks"],
                "balance":info["balance"]
            })
            if "longestchain" in info:
                longestchain = info["longestchain"]
            else:

                longestchain = rpc[ticker].getblockchaininfo()["headers"]
            if longestchain != 0:
                sync_data[ticker].update({
                    "longestchain":longestchain,
                })
            if longestchain == info["blocks"] and longestchain !=0:
                print(ticker+" sync'd on block "+str(longestchain))
                if "last_sync_time" in sync_data[ticker]:
                    if 'tiptime' in info:
                        time_to_sync = int(info["tiptime"]) - int(sync_data[ticker]["last_sync_timestamp"])
                        sync_data[ticker].update({
                            "last_sync_duration":time_to_sync
                        })

                sync_data[ticker].update({
                    "last_sync_block":info["blocks"]
                })
                if 'tiptime' in info:
                    sync_data[ticker].update({
                        "last_sync_timestamp":info["tiptime"],
                        "last_sync_time":time.ctime(info["tiptime"])

                    })
                if ticker in ['AYA', 'GAME', 'GIN', 'EMC2', 'CHIPS']:
                    sync_blockhash = rpc[ticker].getblockhash(int(info["blocks"]))
                else:
                    sync_blockhash = rpc[ticker].getblock(str(info["blocks"]))["hash"]
                sync_data[ticker].update({
                    "last_sync_blockhash": sync_blockhash
                })
                # restart sync of this chain
                logger.info(ticker+" sync'd, restarting")
                clean_chain_data(ticker)
                restart_ticker(ticker)

            if "pubkey" in info:
                sync_data[ticker].update({
                    "pubkey":info["pubkey"]
                })
            else:
                sync_data[ticker].update({
                    "pubkey":"not set"
                })

        except Exception as e:
            print(ticker+" not responding!")
            print(e)
            non_responsive.append(ticker)
        try:
            dexhash = get_dexstats_blockhash(ticker, sync_data[ticker]["last_sync_block"])
            sync_data[ticker].update({
                "last_sync_dexhash":dexhash
            })
        except Exception as e:
            print(ticker+" not avaiable on dexstats")
            print(e)
            sync_data[ticker].update({
                "last_sync_dexhash":"no data"
            })



    # restart unresponsive chains
    sync_data.update({"last_unresponsive":non_responsive})
    for ticker in non_responsive:
        logger.info(ticker+" unresponsive, restarting")
        restart_ticker(ticker)

    # write out sync data to file
    with open('/var/www/html/global_sync.json', 'w+') as f:
        json.dump(sync_data, f, indent=4, sort_keys=True)

