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
from slickrpc import Proxy

r = requests.get('http://notary.earth:8762/api/info/coins/?dpow_active=1')

dpow_coins_info = r.json()['results'][0]
dpow_tickers = []
for ticker in dpow_coins_info:
    dpow_tickers.append(ticker)

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

for ticker in dpow_tickers:
    globals()["assetchain_proxy_{}".format(ticker)] = def_credentials(ticker)

for ticker in dpow_tickers:
    print(globals()["assetchain_proxy_{}".format(ticker)].getinfo())
