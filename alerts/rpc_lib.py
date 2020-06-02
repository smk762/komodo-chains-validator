#!/usr/bin/env python3
import os
import re
import sys
import json
import math
import time
import logging
import platform
import requests
import subprocess
import datetime
from datetime import datetime as dt
from slickrpc import Proxy

from dotenv import load_dotenv
logger = logging.getLogger(__name__)
load_dotenv()

BB_PK = os.getenv("BB_PK")
BB_ADDR = os.getenv("BB_ADDR")

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

r = requests.get('http://notary.earth:8762/api/info/coins/?dpow_active=1')

dpow_coins_info = r.json()['results'][0]
dpow_tickers = []
for ticker in dpow_coins_info:
    dpow_tickers.append(ticker)

rpc = {}

for ticker in dpow_tickers:
    # ignoring btc, not enough space on this server
    if ticker != 'BTC':
        rpc.update({ticker:def_credentials(ticker)})


# need to add dict for start block for each chain.
def get_ntx_txids(ticker, addr, start, end):
    return rpc[ticker].getaddresstxids({"addresses": [BB_ADDR], "start":start, "end":end})

def get_balance_bot_data(chain, txid):
    inputs = {}
    outputs = {}
    while True:
        try:
           raw_tx = rpc[chain].getrawtransaction(txid,1)
           break
        except:
           time.sleep(1)
    src_addr = raw_tx["vin"][0]["address"]
    inputs.update({src_addr:raw_tx["vin"][0]["valueSat"]})
    if src_addr == BB_ADDR:
        block_hash = raw_tx['blockhash']
        block_time = raw_tx['blocktime']
        block_datetime = dt.utcfromtimestamp(raw_tx['blocktime'])
        this_block_height = raw_tx['height']
        vouts = raw_tx["vout"]

        for vout in vouts:
            addr = vout['scriptPubKey']['addresses'][0]
            outputs.update({addr:vout['valueSat']})

    return calc_balance_delta(inputs, outputs)

def calc_balance_delta(inputs, outputs):
    deltas = {}
    for addr in inputs:
        if addr not in deltas:
            val = inputs[addr]
            deltas.update({addr:-1*val})
        else:
            val = deltas[addr]-inputs[addr]
            deltas.update({addr:val})

    for addr in outputs:
        if addr not in deltas:
            val = outputs[addr]
            deltas.update({addr:val})
        else:
            val = deltas[addr]+outputs[addr]
            deltas.update({addr:val})
    return deltas

