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
from . import oraclelib
import logging

logger = logging.getLogger(__name__)

r = requests.get('http://notary.earth:8762/info/coins/?dpow_active=1')

dpow_coins_info = r.json()['results'][0]
dpow_tickers = list(dpow_coins_info.keys())
dpow_tickers.remove('BTC')
logger.info("dpow_tickers: "+str(dpow_tickers))
# create app folders
app_subfolders = ['chains_status', 'ticker_output', 'config']

for folder in app_subfolders:
    if not os.path.exists(sys.path[0]+"/"+folder):
        os.makedirs(sys.path[0]+"/"+folder)

# Set pubkey for oracle chain
if not os.path.isfile(sys.path[0]+'/config/pubkey.txt'):
    with open(sys.path[0]+'/config/pubkey.txt', 'w+') as fp:
        fp.write("")

with open(sys.path[0]+'/config/pubkey.txt', 'r') as fp:
    local_pubkey = fp.read().strip()

if local_pubkey == "":
    logger.warning("You need to define a local pubkey for a valid address in "+oracle_ticker)
    logger.warning("Launch "+oracle_ticker+" with "+" ".join(oracle_launch))
    logger.warning("If running on a Notary Node, import your main node address and use its pubkey!")
    logger.warning("Otherwise, create an address, validate it and input the pubkey in config/pubkey.txt")
    logger.warning("Then ask @smk762#7640 on Discord to send "+oracle_ticker+" funds to cover oracle fees.")
    sys.exit()

# Oracle chain launch params
oracle_ticker = "STATSORCL"
oracle_launch = ['komodod', '-ac_name='+oracle_ticker, '-ac_supply=100000000',
                '-ac_reward=10000000000', '-ac_staked=99', '-ac_cc=762',
                '-ac_halving=762000', '-addnode=116.203.120.91', '-addnode=116.203.120.163', '-pubkey='+local_pubkey]

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
    logger.info(ac_dir)
    if chain in dpow_tickers:
        logger.info(dpow_coins_info[chain])
        if 'conf_path' in dpow_coins_info[chain]['dpow']:
            coin_config_file = str(dpow_coins_info[chain]['dpow']['conf_path'].replace("~",os.environ['HOME']))
        else:
            logger.warning("Conf path not in dpow info for "+chain)
    elif chain == 'KMD':
        coin_config_file = str(ac_dir + '/komodo.conf')
    else:
        coin_config_file = str(ac_dir + '/' + chain + '/' + chain + '.conf')
    logger.info("chain_config: "+coin_config_file)
    if not os.path.isfile(coin_config_file):
        conf_filepath = dpow_coins_info[ticker]['dpow']['conf_path']
        path_file = os.path.split(os.path.abspath(conf_filepath))
        conf_path = path_file[0]
        conf_file = path_file[1]
        if os.path.isfile('~/komodo-chains-validator/confs/'+conf_file):
            shutil.copyfile('~/komodo-chains-validator/confs/'+conf_file, conf_filepath)
    if os.path.isfile(coin_config_file):        
        logger.info("is file")
        with open(coin_config_file, 'r') as f:
            for line in f:
                l = line.rstrip()
                logger.warning(l)
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

for ticker in dpow_tickers:
    globals()["assetchain_proxy_{}".format(ticker)] = def_credentials(ticker)

notary_pubkeys =  {
    "madmax_NA": "0237e0d3268cebfa235958808db1efc20cc43b31100813b1f3e15cc5aa647ad2c3", 
    "alright_AR": "020566fe2fb3874258b2d3cf1809a5d650e0edc7ba746fa5eec72750c5188c9cc9",
    "strob_NA": "0206f7a2e972d9dfef1c424c731503a0a27de1ba7a15a91a362dc7ec0d0fb47685",
    "hunter_EU": "0378224b4e9d8a0083ce36f2963ec0a4e231ec06b0c780de108e37f41181a89f6a", 
    "phm87_SH": "021773a38db1bc3ede7f28142f901a161c7b7737875edbb40082a201c55dcf0add",
    "chainmakers_NA": "02285d813c30c0bf7eefdab1ff0a8ad08a07a0d26d8b95b3943ce814ac8e24d885",
    "indenodes_EU": "0221387ff95c44cb52b86552e3ec118a3c311ca65b75bf807c6c07eaeb1be8303c",
    "blackjok3r_SH": "021eac26dbad256cbb6f74d41b10763183ee07fb609dbd03480dd50634170547cc",
    "chainmakers_EU": "03fdf5a3fce8db7dee89724e706059c32e5aa3f233a6b6cc256fea337f05e3dbf7",
    "titomane_AR": "023e3aa9834c46971ff3e7cb86a200ec9c8074a9566a3ea85d400d5739662ee989",
    "fullmoon_SH": "023b7252968ea8a955cd63b9e57dee45a74f2d7ba23b4e0595572138ad1fb42d21", 
    "indenodes_NA": "02698c6f1c9e43b66e82dbb163e8df0e5a2f62f3a7a882ca387d82f86e0b3fa988",
    "chmex_EU": "0281304ebbcc39e4f09fda85f4232dd8dacd668e20e5fc11fba6b985186c90086e",
    "metaphilibert_SH": "0284af1a5ef01503e6316a2ca4abf8423a794e9fc17ac6846f042b6f4adedc3309",
    "ca333_DEV": "02856843af2d9457b5b1c907068bef6077ea0904cc8bd4df1ced013f64bf267958",
    "cipi_NA": "02858904a2a1a0b44df4c937b65ee1f5b66186ab87a751858cf270dee1d5031f18",
    "pungocloud_SH": "024dfc76fa1f19b892be9d06e985d0c411e60dbbeb36bd100af9892a39555018f6",
    "voskcoin_EU": "034190b1c062a04124ad15b0fa56dfdf34aa06c164c7163b6aec0d654e5f118afb",
    "decker_DEV": "028eea44a09674dda00d88ffd199a09c9b75ba9782382cc8f1e97c0fd565fe5707",
    "cryptoeconomy_EU": "0290ab4937e85246e048552df3e9a66cba2c1602db76e03763e16c671e750145d1",
    "etszombi_EU": "0293ea48d8841af7a419a24d9da11c34b39127ef041f847651bae6ab14dcd1f6b4",  
    "karasugoi_NA": "02a348b03b9c1a8eac1b56f85c402b041c9bce918833f2ea16d13452309052a982",
    "pirate_AR": "03e29c90354815a750db8ea9cb3c1b9550911bb205f83d0355a061ac47c4cf2fde",
    "metaphilibert_AR": "02adad675fae12b25fdd0f57250b0caf7f795c43f346153a31fe3e72e7db1d6ac6",
    "zatjum_SH": "02d6b0c89cacd58a0af038139a9a90c9e02cd1e33803a1f15fceabea1f7e9c263a",
    "madmax_AR": "03c5941fe49d673c094bc8e9bb1a95766b4670c88be76d576e915daf2c30a454d3",
    "lukechilds_NA": "03f1051e62c2d280212481c62fe52aab0a5b23c95de5b8e9ad5f80d8af4277a64b",
    "cipi_AR": "02c4f89a5b382750836cb787880d30e23502265054e1c327a5bfce67116d757ce8",
    "tonyl_AR": "02cc8bc862f2b65ad4f99d5f68d3011c138bf517acdc8d4261166b0be8f64189e1",
    "infotech_DEV": "0345ad4ab5254782479f6322c369cec77a7535d2f2162d103d666917d5e4f30c4c",
    "fullmoon_NA": "032c716701fe3a6a3f90a97b9d874a9d6eedb066419209eed7060b0cc6b710c60b",  
    "etszombi_AR": "02e55e104aa94f70cde68165d7df3e162d4410c76afd4643b161dea044aa6d06ce",
    "node-9_EU": "0372e5b51e86e2392bb15039bac0c8f975b852b45028a5e43b324c294e9f12e411",
    "phba2061_EU": "03f6bd15dba7e986f0c976ea19d8a9093cb7c989d499f1708a0386c5c5659e6c4e",
    "indenodes_AR": "02ec0fa5a40f47fd4a38ea5c89e375ad0b6ddf4807c99733c9c3dc15fb978ee147",
    "and1-89_EU": "02736cbf8d7b50835afd50a319f162dd4beffe65f2b1dc6b90e64b32c8e7849ddd",
    "komodopioneers_SH": "032a238a5747777da7e819cfa3c859f3677a2daf14e4dce50916fc65d00ad9c52a",
    "komodopioneers_EU": "036d02425916444fff8cc7203fcbfc155c956dda5ceb647505836bef59885b6866",
    "d0ct0r_NA": "0303725d8525b6f969122faf04152653eb4bf34e10de92182263321769c334bf58",
    "kolo_DEV": "02849e12199dcc27ba09c3902686d2ad0adcbfcee9d67520e9abbdda045ba83227",
    "peer2cloud_AR": "02acc001fe1fe8fd68685ba26c0bc245924cb592e10cec71e9917df98b0e9d7c37", 
    "webworker01_SH": "031e50ba6de3c16f99d414bb89866e578d963a54bde7916c810608966fb5700776",
    "webworker01_NA": "032735e9cad1bb00eaababfa6d27864fa4c1db0300c85e01e52176be2ca6a243ce",
    "pbca26_NA": "03a97606153d52338bcffd1bf19bb69ef8ce5a7cbdc2dbc3ff4f89d91ea6bbb4dc",
    "indenodes_SH": "0334e6e1ec8285c4b85bd6dae67e17d67d1f20e7328efad17ce6fd24ae97cdd65e",
    "pirate_NA": "0255e32d8a56671dee8aa7f717debb00efa7f0086ee802de0692f2d67ee3ee06ee",
    "lukechilds_AR": "025c6a73ff6d750b9ddf6755b390948cffdd00f344a639472d398dd5c6b4735d23",
    "dragonhound_NA": "0224a9d951d3a06d8e941cc7362b788bb1237bb0d56cc313e797eb027f37c2d375",
    "fullmoon_AR": "03da64dd7cd0db4c123c2f79d548a96095a5a103e5b9d956e9832865818ffa7872",
    "chainzilla_SH": "0360804b8817fd25ded6e9c0b50e3b0782ac666545b5416644198e18bc3903d9f9",
    "titomane_EU": "03772ac0aad6b0e9feec5e591bff5de6775d6132e888633e73d3ba896bdd8e0afb", 
    "jeezy_EU": "037f182facbad35684a6e960699f5da4ba89e99f0d0d62a87e8400dd086c8e5dd7",
    "titomane_SH": "03850fdddf2413b51790daf51dd30823addb37313c8854b508ea6228205047ef9b",
    "alien_AR": "03911a60395801082194b6834244fa78a3c30ff3e888667498e157b4aa80b0a65f",
    "pirate_EU": "03fff24efd5648870a23badf46e26510e96d9e79ce281b27cfe963993039dd1351",
    "thegaltmines_NA": "02db1a16c7043f45d6033ccfbd0a51c2d789b32db428902f98b9e155cf0d7910ed",
    "computergenie_NA": "03a78ae070a5e9e935112cf7ea8293f18950f1011694ea0260799e8762c8a6f0a4",
    "nutellalicka_SH": "02f7d90d0510c598ce45915e6372a9cd0ba72664cb65ce231f25d526fc3c5479fc",
    "chainstrike_SH": "03b806be3bf7a1f2f6290ec5c1ea7d3ea57774dcfcf2129a82b2569e585100e1cb",
    "hunter_SH": "02407db70ad30ce4dfaee8b4ae35fae88390cad2b0ba0373fdd6231967537ccfdf", 
    "alien_EU": "03bb749e337b9074465fa28e757b5aa92cb1f0fea1a39589bca91a602834d443cd", 
    "gt_AR": "0348430538a4944d3162bb4749d8c5ed51299c2434f3ee69c11a1f7815b3f46135",
    "patchkez_SH": "03f45e9beb5c4cd46525db8195eb05c1db84ae7ef3603566b3d775770eba3b96ee",
    "decker_AR": "03ffdf1a116300a78729608d9930742cd349f11a9d64fcc336b8f18592dd9c91bc"
}
validator_pubkeys =  {
    "SYNC_24": "02317cf599fb502d96ac36fa239f9cf308825738fbbe0d3237f783f895ab4e5fee", 
}

kmd_dir = os.environ['HOME'] + '/.komodo'

if not os.path.isfile(sys.path[0]+'/chains_status/global_sync.json'):
    sync_status = {}
else:
    with open(sys.path[0]+'/chains_status/global_sync.json', 'r') as fp:
        sync_status = json.loads(fp.read())

# sync chains
def sim_chains_start_and_sync():
    launch_stats_oracle(oracle_ticker)
    stats_orcl_info = get_node_oracle(oracle_ticker)
    # start with creating a proxy for each assetchain
    for ticker in dpow_tickers:
        # 30 sec wait during restart for getting rpc credentials
        # 30 sec * approx. 40 chains = 20 min to start
        restart_ticker(ticker)
        logger.debug(globals())
        if ticker not in sync_status:
            sync_status.update({ticker:{}})
    while True:
        update_oracle = False
        for ticker in dpow_tickers:
            try:
                ticker_rpc = globals()["assetchain_proxy_{}".format(ticker)]
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
                    update_oracle = True
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
        if update_oracle:
            oracle_rpc = globals()["assetchain_proxy_{}".format(oracle_ticker)]
            oraclelib.write2oracle(oracle_rpc, stats_orcl_info['txid'], str(sync_status))
        # loop again in 15 min
        time.sleep(900)
    return True

# Clean ticker data folder
def clean_chain_data(ticker):
    stop_result = globals()["assetchain_proxy_{}".format(ticker)].stop()
    logger.info(ticker + " stopped!")
    time.sleep(30)
    conf_filepath = dpow_coins_info[ticker]['dpow']['conf_path']
    path_file = os.path.split(os.path.abspath(conf_filepath))
    conf_path = path_file[0]
    conf_file = path_file[1]
    shutil.rmtree(conf_path)
    logger.info(conf_path+" deleted")
    # some 3P chains do not create a conf, will need to do this manually by copying ./confs/{chain}.conf into required folder.
    os.makedirs(conf_path)
    if os.path.isfile('~/komodo-chains-validator/confs/'+conf_file):
        shutil.copyfile('~/komodo-chains-validator/confs/'+conf_file, conf_filepath)


def restart_ticker(ticker):
    try:
        logger.info("restarting "+ticker)
        ticker_launch = dpow_coins_info[ticker]['dpow']['launch_params'] \
                        .replace("~",os.environ['HOME']).split(' ')
        ticker_output = open(sys.path[0]+'/ticker_output/'+ticker+"_output.log",'w+')
        subprocess.Popen(ticker_launch, stdout=ticker_output, stderr=ticker_output, universal_newlines=True)
        logger.info("sleeping 30 sec")
        time.sleep(30)
        logger.info("Setting RPC for "+ticker)
        globals()["assetchain_proxy_{}".format(ticker)] = def_credentials(ticker)
        logger.debug("globals: "+str(globals()))
    except Exception as e:
        logger.debug("error restarting ticker "+ticker+": "+str(e))


def launch_stats_oracle(oracle_ticker):
    ticker_output = open(sys.path[0]+'/ticker_output/'+oracle_ticker+"_output.log",'w+')
    logger.info("starting "+oracle_ticker)
    subprocess.Popen(oracle_launch, stdout=ticker_output, stderr=ticker_output, universal_newlines=True)
    time.sleep(15)
    globals()["assetchain_proxy_{}".format(oracle_ticker)] = def_credentials(oracle_ticker)

def get_node_oracle(oracle_ticker):
    if not os.path.isfile(sys.path[0]+'/config/oracle.json'):
        local_oracle_params = {}
        orcl_info = create_node_oracle(oracle_ticker)
        with open(sys.path[0]+'/config/oracle.json', 'w+') as fp:
            json.dump(orcl_info, fp, indent=4)
        logger.info("Saved oracle info data to "+sys.path[0]+"/config/oracle.json")
    with open(sys.path[0]+'/config/oracle.json', 'r') as fp:
        orcl_info = json.loads(fp.read())
    return orcl_info

def get_local_node_name():
    node_name = ''
    logger.info("Checking if ["+local_pubkey+"] in notary_pubkeys")
    for node in list(notary_pubkeys.keys()):
        if notary_pubkeys[node] == local_pubkey:
            node_name = node
            break
    if node_name == '':
        logger.info("Checking if ["+local_pubkey+"] in validator_pubkeys")
        for node in list(validator_pubkeys.keys()):
            if validator_pubkeys[node] == local_pubkey:
                node_name = node
                break
    return node_name

def create_node_oracle(oracle_ticker):
    node_name = get_local_node_name()
    if node_name != '':
        logger.info("Welcome "+node_name+"!")
        logger.info("Creating your oracle...")
        try:
            oracle_ticker_rpc = globals()["assetchain_proxy_{}".format(oracle_ticker)]
            get_info = oracle_ticker_rpc.getinfo()
            get_info_pubkey = get_info['pubkey']
            get_info_balance = get_info['balance']
            if get_info_pubkey == local_pubkey:
                if get_info_balance < 10:
                    logger.warning("Oracle creation aborted: "+oracle_ticker+" has insufficient funds (10005 required)")
                    logger.warning("Ask @smk762#7640 on Discord to send some.")
                    sys.exit()
                else:
                    oracle_txid = oraclelib.create_oracle(oracle_ticker, oracle_ticker_rpc,
                                                          node_name+"_blockhash_stats",
                                                          node_name+" blockhash stats", 'S', 0.001)
                    orcl_info = oracle_ticker_rpc.oraclesinfo(oracle_txid)
                    return orcl_info
            else:
                logger.warning("Oracle creation aborted: "+oracle_ticker+" not launched with pubkey ["+local_pubkey+"]")
                sys.exit()
        except Exception as e:
            logger.warning("Oracle creation failed: "+str(e))
            logger.warning("Did you launch "+oracle_ticker+" with pubkey ["+local_pubkey+"]?")
            sys.exit()
    else:
        logger.warning("Oracle creation aborted: pubkey ["+local_pubkey+"] not recognised in notary / validator pubkeys dicts.")
        logger.warning("Submit a Pull Request to add it...")
        sys.exit()

def get_sync_node_data():
    # Get sync node's latest hashes
    sync_data = {}
    rpc_proxy = def_credentials(oracle_ticker)
    oracle_txid = 'b4fef41d11b6aab51b77945d3df7cdaeb9148dfa4df1e56d2057ec0d4cdab8c4'
    baton = 'RSGFUXm7cYe4h3u312qmtVnyHJnVqpS1EJ'
    samples = rpc_proxy.oraclessamples(oracle_txid, baton, str(1))
    if samples['result'] == 'success':
        if len(samples['samples'][0]['data']) > 0:
            sync_data = json.loads(samples['samples'][0]['data'][0].replace("\'", "\""))
    return sync_data

def report_nn_tip_hashes():
    launch_stats_oracle(oracle_ticker)
    stats_orcl_info = get_node_oracle(oracle_ticker)
    # start with creating a proxy for each assetchain
    for ticker in dpow_tickers:
        globals()["assetchain_proxy_{}".format(ticker)] = def_credentials(ticker)
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
                ticker_rpc = globals()["assetchain_proxy_{}".format(ticker)]
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
        # write notary hashes to oracle
        if this_node_update_time < sync_node_update_time:
            this_node_update_time = int(time.time())
            oracle_rpc = globals()["assetchain_proxy_{}".format(oracle_ticker)]
            oraclelib.write2oracle(oracle_rpc, stats_orcl_info['txid'], str(sync_status))
            logger.info("Global sync_status data written to oracle ["+stats_orcl_info['txid']+"]")
        else:
            logger.info("Global sync_status data not written to oracle, waiting for sync node update.")
            logger.info("sync_node_update_time: "+str(sync_node_update_time))
            logger.info("this_node_update_time: "+str(this_node_update_time))
        time.sleep(600)
    return True

