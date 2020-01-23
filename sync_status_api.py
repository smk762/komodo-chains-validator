#!/usr/bin/env python3
from typing import Optional, List
from fastapi import Depends, FastAPI, HTTPException
from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
#from pydantic import BaseModel, Field
from starlette.status import HTTP_401_UNAUTHORIZED
from threading import Thread
#import sqlite3
import datetime
from lib import validator_lib, oraclelib
import uvicorn
import uvicorn.protocols
import uvicorn.lifespan
import uvicorn.lifespan.on
import uvicorn.protocols.http
import uvicorn.protocols.websockets
import uvicorn.protocols.websockets.auto
import uvicorn.protocols.http.auto
import uvicorn.logging
import uvicorn.loops
import uvicorn.loops.auto
import time
import json
import sys
import os
import logging

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%d-%b-%y %H:%M:%S')

fh = logging.FileHandler(sys.path[0]+'/sync_api.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.addHandler(fh)
logger.setLevel(logging.INFO)

rpc_proxy = validator_lib.def_credentials(validator_lib.oracle_ticker)
ignore_oracles = []

def get_hashtip_oracles():
    # get oracles list
    hashtip_oracles = {}
    oracles_list = rpc_proxy.oracleslist()
    # check oracle name / publishers
    for oracle_txid in oracles_list:
        if oracle_txid not in ignore_oracles:
            oracle_info = rpc_proxy.oraclesinfo(oracle_txid)
            try:
                desc = oracle_info['description'].split()
                if desc[1] == 'blockhash' and desc[2] == 'stats':
                    node_name = desc[0]
                publishers = oracle_info['registered']
                for publisher in publishers:
                    pubkey = publisher['publisher']
                    if node_name in validator_lib.notary_pubkeys:
                        if pubkey == validator_lib.notary_pubkeys[node_name]:
                            hashtip_oracles.update({
                                node_name: {
                                    "oracle_txid":oracle_info['txid'],
                                    "publisher":pubkey,
                                    "baton":publisher['baton'],
                                    "funds":publisher['funds'],                        
                                    "node_type":"notary",
                                }
                            })
                    elif node_name in validator_lib.validator_pubkeys:
                        if pubkey == validator_lib.validator_pubkeys[node_name]:
                            hashtip_oracles.update({
                                node_name: {
                                    "oracle_txid":oracle_info['txid'],
                                    "publisher":pubkey,
                                    "baton":publisher['baton'],
                                    "funds":publisher['funds'],                        
                                    "node_type":"sync_loop",
                                }
                            })
            except Exception as e:
                logger.warning("Error getting hashtip oracle: "+str(e))
                logger.warning(node_name+" Oracle TXID: "+str(oracle_txid))
                logger.warning(node_name+" Oracle info: "+str(oracle_info))
    return hashtip_oracles

def get_hashtips():
    hashtips = {}
    node_name_update = {}
    hashtip_oracles = get_hashtip_oracles()
    for node_name in hashtip_oracles:
        try:
            oracle_txid = hashtip_oracles[node_name]["oracle_txid"]
            baton = hashtip_oracles[node_name]["baton"]
            samples = rpc_proxy.oraclessamples(oracle_txid, baton, str(1))
            if samples['result'] == 'success':
                if len(samples['samples'][0]['data']) > 0:
                    sample_data = json.loads(samples['samples'][0]['data'][0].replace("\'", "\""))
                    ticker_names = list(sample_data.keys())
                    ticker_names.sort()
                    for ticker in ticker_names:
                        if ticker == 'last_updated':
                            if 'last_updated' not in hashtips:
                                hashtips.update({'last_updated':{}})
                            hashtips['last_updated'].update({node_name:sample_data['last_updated']})
                        else:
                            try:
                                tip_block = str(sample_data[ticker]['last_longestchain'])
                                tip_hash = sample_data[ticker]['last_longesthash']
                                tip_updated = sample_data[ticker]['last_updated']

                                if ticker not in hashtips:
                                    hashtips.update({ticker:{}})
                                if ticker not in node_name_update:
                                    node_name_update.update({ticker:tip_updated})

                                # ignore dead oracles with same node_name
                                if tip_updated >= node_name_update[ticker]:
                                    if tip_block not in hashtips[ticker]:
                                        hashtips[ticker].update({tip_block:{}})
                                    if tip_hash not in hashtips[ticker][tip_block]:
                                        hashtips[ticker][tip_block].update({tip_hash:[]})
                                    # add node_name to ticker / block / hash list
                                    nodes_on_hash = hashtips[ticker][tip_block][tip_hash]
                                    nodes_on_hash.append(node_name)
                                    hashtips[ticker][tip_block].update({tip_hash:nodes_on_hash})
                                    # set latest update time for node_name / ticker
                                    node_name_update.update({ticker:tip_updated})
                            except Exception as e:
                                pass
                                # this can happen for unsynced chains on the looper
                                #logger.warning("Error getting hashtip for "+node_name+"/"+ticker+": "+str(e))
        except Exception as e:
            logger.warning("Error getting hashtip: "+str(e))
    return hashtips

### API CALLS

app = FastAPI()
@app.get("/")
async def root():
    return {"message": "Welcome to Sync Status API. See /docs for all methods"}

@app.get("/api_version")
async def api_version():
    return {"version": "0.0.2"}

@app.get("/show_hashtip_oracles")
async def show_hashtip_oracles():
    return get_hashtip_oracles()

@app.get("/show_hashtips")
async def show_hashtips():
    return get_hashtips()

@app.get("/show_sync_node_data")
async def show_sync_node_data():
    return validator_lib.get_sync_node_data()

@app.get("/chains_monitored")
async def chains_monitored():
    return {"version": "0.0.2"}

@app.get("/node_sync_stats/{node_name}")
async def node_sync_stats(node_name: str = "ALL"):
    return {"version": "0.0.2"}

@app.get("/chain_sync_stats/{ticker}")
async def chain_sync_stats(ticker: str = "ALL"):
    return {"version": "0.0.2"}

if __name__ == "__main__":
    format = '%(asctime)s %(levelname)-8s %(message)s'
    uvicorn.run(app, host="127.0.0.1", port=8000, forwarded_allow_ips='138.201.207.24')
