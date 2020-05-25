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

class BTC_CoinParams(CoreMainParams):
    MESSAGE_START = b'\x24\xe9\x27\x64'
    DEFAULT_PORT = 7770
    BASE58_PREFIXES = {'PUBKEY_ADDR': 0,
                       'SCRIPT_ADDR': 5,
                       'SECRET_KEY': 128}

def get_from_electrum(url, port, method, params=[]):
    try:
        params = [params] if type(params) is not list else params
        socket.setdefaulttimeout(5)
        s = socket.create_connection((url, port))
        s.send(json.dumps({"id": 0, "method": method, "params": params}).encode() + b'\n')
        return json.loads(s.recv(99999)[:-1].decode())
    except Exception as e:
        print("==============================")
        print(str(url)+""+str(port)+" failed!")
        print(e)
        print("==============================")

def lil_endian(hex_str):
    return ''.join([hex_str[i:i+2] for i in range(0, len(hex_str), 2)][::-1])

def get_addr_from_pubkey(pubkey):
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
    print(p2pk_resp)
    p2pkh_resp = get_from_electrum(url, port, 'blockchain.scripthash.get_balance', p2pkh_scripthash)
    print(p2pkh_resp)
    p2pk_confirmed_balance = p2pk_resp['result']['confirmed']
    p2pkh_confirmed_balance = p2pkh_resp['result']['confirmed']
    p2pk_unconfirmed_balance = p2pk_resp['result']['unconfirmed']
    p2pkh_unconfirmed_balance = p2pkh_resp['result']['unconfirmed']
    total_confirmed = p2pk_confirmed_balance + p2pkh_confirmed_balance
    total_unconfirmed = p2pk_unconfirmed_balance + p2pkh_unconfirmed_balance
    total = total_confirmed + total_unconfirmed
    return total
