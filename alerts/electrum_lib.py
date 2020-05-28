#!/usr/bin/env python3
import requests
import socket
import json
import time
import hashlib
import codecs
import base58
import logging
import logging.handlers
from logging import Handler, Formatter
import bitcoin
from bitcoin.core import x
from bitcoin.core import CoreMainParams
from bitcoin.wallet import P2PKHBitcoinAddress

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%d-%b-%y %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class KMD_CoinParams(CoreMainParams):
    MESSAGE_START = b'\x24\xe9\x27\x64'
    DEFAULT_PORT = 7770
    BASE58_PREFIXES = {'PUBKEY_ADDR': 60,
                       'SCRIPT_ADDR': 85,
                       'SECRET_KEY': 188}

class BTC_CoinParams(CoreMainParams):
    MESSAGE_START = b'\x24\xe9\x27\x64'
    DEFAULT_PORT = 7770
    BASE58_PREFIXES = {'PUBKEY_ADDR': 0,
                       'SCRIPT_ADDR': 5,
                       'SECRET_KEY': 128}

class AYA_CoinParams(CoreMainParams):
    MESSAGE_START = b'\x24\xe9\x27\x64'
    DEFAULT_PORT = 7770
    BASE58_PREFIXES = {'PUBKEY_ADDR': 23,
                       'SCRIPT_ADDR': 5,
                       'SECRET_KEY': 176}

class EMC2_CoinParams(CoreMainParams):
    MESSAGE_START = b'\x24\xe9\x27\x64'
    DEFAULT_PORT = 7770
    BASE58_PREFIXES = {'PUBKEY_ADDR': 33,
                       'SCRIPT_ADDR': 5,
                       'SECRET_KEY': 176}

class GAME_CoinParams(CoreMainParams):
    MESSAGE_START = b'\x24\xe9\x27\x64'
    DEFAULT_PORT = 7770
    BASE58_PREFIXES = {'PUBKEY_ADDR': 38,
                       'SCRIPT_ADDR': 5,
                       'SECRET_KEY': 166}

class GIN_CoinParams(CoreMainParams):
    MESSAGE_START = b'\x24\xe9\x27\x64'
    DEFAULT_PORT = 7770
    BASE58_PREFIXES = {'PUBKEY_ADDR': 38,
                       'SCRIPT_ADDR': 10,
                       'SECRET_KEY': 198}

# Update this if new third party coins added
coin_params = {
    "KMD": KMD_CoinParams,
    "BTC": BTC_CoinParams,
    "AYA": AYA_CoinParams,
    "EMC2": EMC2_CoinParams,
    "GAME": GAME_CoinParams,
    "GIN": GIN_CoinParams,
}

# Get 3rd party / main dPoW coins
all_coins = []
main_coins = []
third_party_coins = []

r = requests.get("https://raw.githubusercontent.com/KomodoPlatform/dPoW/master/README.md")
dpow_readme = r.text
lines = dpow_readme.splitlines()
for line in lines:
    if line.find('dPoW-mainnet') != -1 or line.find('dPoW-3P') != -1:
        raw_info = line.split("|")
        info = [i.strip() for i in raw_info]
        coin = info[0]
        server = info[4]
        all_coins.append(coin)
        if server.lower() == 'dpow-mainnet':
            main_coins.append(coin)
        elif server.lower() == 'dpow-3p':
            third_party_coins.append(coin)
        else:
            logger.info("UNRECOGNISED SERVER VALUE: "+server)

main_coins = main_coins[:]+['BTC']
third_party_coins = third_party_coins[:]+['KMD']
antara_coins = main_coins[:]+['HUSH3', 'CHIPS', 'MCL']
all_coins = third_party_coins[:]+main_coins

main_coins.sort()
third_party_coins.sort()
antara_coins.sort()
all_coins.sort()

for coin in antara_coins:
    coin_params.update({coin:KMD_CoinParams})

electrums = {}
r = requests.get('http://notary.earth:8762/api/info/coins/?dpow_active=1')
coins_info = r.json()
for coin in coins_info['results'][0]:
    if len(coins_info['results'][0][coin]['electrums']) > 0:
        electrum = coins_info['results'][0][coin]['electrums'][0].split(":") 
        electrums.update({
            coin:{
                "url":electrum[0],
                "port":electrum[1]
                }
            })

def get_from_electrum(url, port, method, params=[]):
    try:
        params = [params] if type(params) is not list else params
        socket.setdefaulttimeout(5)
        s = socket.create_connection((url, port))
        s.send(json.dumps({"id": 0, "method": method, "params": params}).encode() + b'\n')
        return json.loads(s.recv(99999)[:-1].decode())
    except Exception as e:
        logger.info("==============================")
        logger.info(str(url)+""+str(port)+" failed!")
        logger.info(e)
        logger.info("==============================")

def lil_endian(hex_str):
    return ''.join([hex_str[i:i+2] for i in range(0, len(hex_str), 2)][::-1])

def get_addr_from_pubkey(pubkey, coin):
    bitcoin.params = coin_params[coin]
    return str(P2PKHBitcoinAddress.from_pubkey(x(pubkey)))

def get_p2pk_scripthash_from_pubkey(pubkey):
    scriptpubkey = '21' +pubkey+ 'ac'
    scripthex = codecs.decode(scriptpubkey, 'hex')
    s = hashlib.new('sha256', scripthex).digest()
    sha256_scripthash = codecs.encode(s, 'hex').decode("utf-8")
    script_hash = lil_endian(sha256_scripthash)
    return script_hash

def get_p2pkh_scripthash_from_pubkey(pubkey):
    publickey = codecs.decode(pubkey, 'hex')
    s = hashlib.new('sha256', publickey).digest()
    r = hashlib.new('ripemd160', s).digest()
    scriptpubkey = "76a914"+codecs.encode(r, 'hex').decode("utf-8")+"88ac"
    h = codecs.decode(scriptpubkey, 'hex')
    s = hashlib.new('sha256', h).digest()
    sha256_scripthash = codecs.encode(s, 'hex').decode("utf-8")
    script_hash = lil_endian(sha256_scripthash)
    return script_hash

def get_full_electrum_balance(pubkey, url, port):
    p2pk_scripthash = get_p2pk_scripthash_from_pubkey(pubkey)
    p2pkh_scripthash = get_p2pkh_scripthash_from_pubkey(pubkey)
    p2pk_resp = get_from_electrum(url, port, 'blockchain.scripthash.get_balance', p2pk_scripthash)
    logger.info(p2pk_resp)
    p2pkh_resp = get_from_electrum(url, port, 'blockchain.scripthash.get_balance', p2pkh_scripthash)
    logger.info(p2pkh_resp)
    p2pk_confirmed_balance = p2pk_resp['result']['confirmed']
    p2pkh_confirmed_balance = p2pkh_resp['result']['confirmed']
    p2pk_unconfirmed_balance = p2pk_resp['result']['unconfirmed']
    p2pkh_unconfirmed_balance = p2pkh_resp['result']['unconfirmed']
    total_confirmed = p2pk_confirmed_balance + p2pkh_confirmed_balance
    total_unconfirmed = p2pk_unconfirmed_balance + p2pkh_unconfirmed_balance
    total = total_confirmed + total_unconfirmed
    return total/100000000

def get_dexstats_balance(chain, addr):
    url = 'http://'+chain.lower()+'.explorer.dexstats.info/insight-api-komodo/addr/'+addr
    r = requests.get(url)
    balance = r.json()['balance']
    return balance

def get_balance(chain, addr, pubkey):
    balance = -1
    try:
        if chain in electrums:
            try:
                url = electrums[chain]["url"]
                port = electrums[chain]["port"]
                source = url+":"+str(port)
                balance = get_full_electrum_balance(pubkey, url, port)
            except Exception as e:
                print(chain+" "+source+" ERR: "+str(e))
                try:
                    source = "dexstats"
                    balance = get_dexstats_balance(chain, addr)
                except Exception as e:
                    print(chain+" "+source+" ERR: "+str(e))

        elif chain in antara_coins:
            try:
                source = "dexstats"
                balance = get_dexstats_balance(chain, addr)
            except Exception as e:
                print(chain+" "+source+" ERR: "+str(e))

        elif chain == "GIN":
            print("gin is dead?")
            source = "None"
        elif chain == "AYA":
            url = 'https://explorer.aryacoin.io/ext/getaddress/'+addr
            r = requests.get(url)
            try:
                source = 'explorer.aryacoin.io'
                balance = r.json()['balance']
            except Exception as e:
                print(chain+" "+source+" ERR: "+str(e))

    except Exception as e:
        print("get_balance ERR: "+str(e))
    if balance != -1:
        print("<<<<< "+chain+" via ["+source+"] OK | addr: "+addr+" | balance: "+str(balance))
    else:
        print("##### "+chain+" via ["+source+"] FAILED | addr: "+addr+" | balance: "+str(balance))
    return balance, source
