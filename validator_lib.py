from slickrpc import Proxy
import time
import subprocess
import platform
import os
import re


def def_credentials(chain):
    rpcport = ''
    ac_dir = ''
    operating_system = platform.system()
    if operating_system == 'Darwin':
        ac_dir = os.environ['HOME'] + '/Library/Application Support/Komodo'
    elif operating_system == 'Linux':
        ac_dir = os.environ['HOME'] + '/.komodo'
    elif operating_system == 'Win64' or operating_system == 'Windows':
        ac_dir = '%s/komodo/' % os.environ['APPDATA']
    if chain == 'KMD':
        coin_config_file = str(ac_dir + '/komodo.conf')
    else:
        coin_config_file = str(ac_dir + '/' + chain + '/' + chain + '.conf')
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
            print("check "+coin_config_file)
            exit(1)

    return Proxy("http://%s:%s@127.0.0.1:%d" % (rpcuser, rpcpassword, int(rpcport)))

ac_tickers = ["REVS", "SUPERNET", "DEX", "PANGEA", "JUMBLR", "BET", "CRYPTO", "HODL", "MSHARK", "BOTS", "MGW", "COQUICASH", "WLC", "KV",
              "CEAL", "MESH", "AXO", "ETOMIC", "BTCH", "NINJA", "OOT", "BNTN", "CHAIN", "PRLPAY", "DSEC", "EQL", "ZILLA", "RFOX", "SEC",
              "CCL", "PIRATE", "PGT", "KMDICE", "DION", "KSB", "OUR", "ILN", "RICK", "MORTY", "KOIN", "ZEXO", "K64", "HUSH3", "THC", "COMMOD", "WLC21"]

# sync chains
def chains_start_and_sync():
    # starting assetchains daemons
    subprocess.run(["./assetchains.old"])
    # creating a proxy for each assetchain
    for ticker in ac_tickers:
        globals()["assetchain_proxy_{}".format(ticker)] = def_credentials(ticker)
    # waiting until assetchains are synced
    while True:
        are_all_chains_synced = True
        for ticker in ac_tickers:
            get_info_result = globals()["assetchain_proxy_{}".format(ticker)].getinfo()
            if get_info_result["blocks"] < get_info_result["longestchain"]:
                print("Chain " + ticker + " is NOT synced. Blocks: " + str(get_info_result["blocks"]) + " Longestchain: " + str(get_info_result["longestchain"]))
                are_all_chains_synced = False
            else:
                print("Chain " + ticker + " is synced. Blocks: " + str(get_info_result["blocks"]) + " Longestchain: " + str(get_info_result["longestchain"]))
        if are_all_chains_synced:
            print("All chains are on sync now!")
            break
        else:
            ("Chain are not synced yet")
            time.sleep(60)
    return True

# write down state

# clean everything

# repeat chains sync