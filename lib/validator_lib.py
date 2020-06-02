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

BB_PK = os.getenv("BB_PK")
BB_PK = os.getenv("BB_PUB")

main_server_only = False

logger = logging.getLogger(__name__)

r = requests.get('http://notary.earth:8762/api/info/coins/?dpow_active=1')

dpow_coins_info = r.json()['results'][0]
dpow_tickers = []
for ticker in dpow_coins_info:
    if main_server_only:
        if dpow_coins_info[ticker]['dpow']['server'] == 'dPoW-mainnet':
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
    elif chain == 'KMD':
        coin_config_file = str(ac_dir + '/komodo.conf')
    else:
        coin_config_file = str(ac_dir + '/' + chain + '/' + chain + '.conf')
    if not os.path.isfile(coin_config_file):
        conf_filepath = dpow_coins_info[ticker]['dpow']['conf_path']
        path_file = os.path.split(os.path.abspath(conf_filepath))
        conf_file = path_file[1]
        if os.path.isfile(os.environ['HOME']+'/komodo-chains-validator/confs/'+conf_file):
            shutil.copyfile(os.environ['HOME']+'/komodo-chains-validator/confs/'+conf_file, coin_config_file)
    if os.path.isfile(coin_config_file):        
        logger.info("is file")
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
    rpc[ticker] = def_credentials(ticker)

kmd_dir = os.environ['HOME'] + '/.komodo'

if not os.path.isfile(sys.path[0]+'/chains_status/global_sync.json'):
    sync_status = {}
else:
    with open(sys.path[0]+'/chains_status/global_sync.json', 'r') as fp:
        sync_status = json.loads(fp.read())

# sync chains
def sim_chains_start_and_sync():
    # start with creating a proxy for each assetchain
    for ticker in dpow_tickers:
        # 60 sec wait during restart for getting rpc credentials
        # 60 sec * approx. 40 chains = 40 min to start
        restart_ticker(ticker)
        if ticker not in sync_status:
            sync_status.update({ticker:{}})
    while True:
        for ticker in dpow_tickers:
            try:
                ticker_rpc = rpc[ticker]
                ticker_timestamp = int(time.time())
                sync_status[ticker].update({"last_updated":ticker_timestamp})
                get_info_result = ticker_rpc.getinfo()
                sync_status[ticker].update({
                        "blocks":get_info_result["blocks"],
                        "longestchain":get_info_result["longestchain"]
                    })
                if get_info_result["blocks"] < get_info_result["longestchain"] or get_info_result["longestchain"] == 0:
                    logger.info(colorize("Chain " + ticker + " is NOT synced."
                                 + " Blocks: " + str(get_info_result["blocks"]) 
                                 + " Longestchain: " + str(get_info_result["longestchain"]),
                                   "red"))
                else:
                    logger.info(colorize("Chain " + ticker + " is synced."
                                + " Blocks: " + str(get_info_result["blocks"])
                                + " Longestchain: " + str(get_info_result["longestchain"])
                                + " Latest Blockhash: " + ticker_rpc.getblock(str(get_info_result["blocks"]))["hash"],
                                  "green"))
                    latest_block_fifth = int(math.floor(get_info_result["longestchain"]/5)*5)
                    latest_block_fifth_hash = ticker_rpc.getblock(str(latest_block_fifth))["hash"]
                    sync_status[ticker].update({
                            "last_longesthash":latest_block_fifth_hash,
                            "last_longestchain":latest_block_fifth
                        })
                    # save timestamped file for ticker if synced
                    filename = ticker+'_sync_'+str(ticker_timestamp)+'.json'
                    with open(sys.path[0]+'/chains_status/' + filename, 'w+') as fp:
                        json.dump(sync_status[ticker], fp, indent=4)
                    logger.info("Saved "+ticker+" sync data to " + filename)
                    clean_chain_data(ticker)
                    restart_ticker(ticker)
            except Exception as e:
                logger.info(e)
        # save global state file
        sync_status.update({"last_updated":ticker_timestamp})
        with open(sys.path[0]+'/chains_status/global_sync.json', 'w+') as fp:
            json.dump(sync_status, fp, indent=4)
        logger.info("Saved global state data to global_sync.json")
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
    conf_path = path_file[0]
    conf_file = path_file[1]

    # not removing confs or wallets
    shutil.rmtree(conf_path+"/blocks")
    shutil.rmtree(conf_path+"/database")
    shutil.rmtree(conf_path+"/chainstate")
    shutil.rmtree(conf_path+"/notarisations")

    logger.info(conf_path+" subfolders deleted")
    # some 3P chains do not create a conf, will need to do this manually by copying ./confs/{chain}.conf into required folder.
    if os.path.isfile(os.environ['HOME']+'/komodo-chains-validator/confs/'+conf_file):
        shutil.copyfile(os.environ['HOME']+'/komodo-chains-validator/confs/'+conf_file, conf_filepath)

def restart_ticker(ticker):
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
    if os.path.exists(sys.path[0]+'/chains_status/global_sync.json'):
        with open(sys.path[0]+'/chains_status/global_sync.json', 'w+') as f:
            json.dump(sync_data, f, indent=4)
    return sync_data

def report_nn_tip_hashes():
    # start with creating a proxy for each assetchain
    for ticker in dpow_tickers:
        rpc[ticker] = def_credentials(ticker)
        sync_status.update({ticker:{}})
    this_node_update_time = 0
    while True:
        # read sync node data
        sync_data = get_sync_node_data()
        sync_node_update_time = sync_data['last_updated']
        for ticker in dpow_tickers:
            try:
                # compare sync node hash to local hash
                sync_ticker_data = sync_data[ticker]
                sync_ticker_block = sync_ticker_data['last_longestchain']
                sync_ticker_hash = sync_ticker_data['last_longesthash']
                ticker_rpc = rpc[ticker]
                ticker_timestamp = int(time.time())
                sync_status[ticker].update({"last_updated":ticker_timestamp})
                get_info_result = ticker_rpc.getinfo()
                sync_status[ticker].update({
                        "blocks":get_info_result["blocks"],
                        "longestchain":get_info_result["longestchain"]
                    })
                if get_info_result["blocks"] < get_info_result["longestchain"]:
                    logger.info(colorize("Chain " + ticker + " is NOT synced."
                                + " Blocks: " + str(get_info_result["blocks"])
                                + " Longestchain: "+ str(get_info_result["longestchain"]),
                                  "red"))
                else:
                    logger.info(colorize("Chain " + ticker + " is synced."
                                + " Blocks: " + str(get_info_result["blocks"])
                                + " Longestchain: " + str(get_info_result["longestchain"])
                                + " Latest Blockhash: " + ticker_rpc.getblock(str(get_info_result["blocks"]))["hash"],
                                  "green"))
                    ticker_sync_block_hash = ticker_rpc.getblock(str(sync_ticker_block))["hash"]
                    sync_status[ticker].update({
                            "last_longesthash":ticker_sync_block_hash,
                            "last_longestchain":sync_ticker_block
                        })
                if ticker_sync_block_hash == sync_ticker_hash:
                    # all good
                    logger.info(colorize("Sync node comparison for "+ticker+" block ["+str(sync_ticker_block)+"] MATCHING! ", 'green'))
                    logger.info(colorize("Hash: ["+sync_ticker_hash+"]", 'green'))
                else:
                    # possible fork
                    logger.warning(colorize("Sync node comparison for "+ticker+" block ["+str(sync_ticker_block)+"] FAILED! ", "red"))
                    logger.warning(colorize("Sync node hash: ["+sync_ticker_hash+"]", 'red'))
                    logger.warning(colorize("Notary node hash: ["+ticker_sync_block_hash+"]", 'red'))
            except Exception as e:
                logger.warning(ticker+" error: "+str(e))
                logger.info(ticker+" sync data: "+str(sync_ticker_data))
            time.sleep(1)
        # save global state file
        sync_status.update({"last_updated":ticker_timestamp})
        with open(sys.path[0]+'/chains_status/global_sync.json', 'w+') as fp:
            json.dump(sync_status, fp, indent=4)
        logger.info("Saved global state data to global_sync.json")
        time.sleep(600)
    return True

# last sync'd at time/block
# time taken to sync
# time since restart
# current sync pct
# current block