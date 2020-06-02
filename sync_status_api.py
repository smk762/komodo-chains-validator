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
from lib import validation_lib, oraclelib
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

### API CALLS

app = FastAPI()
@app.get("/")
async def root():
    return {"message": "Welcome to Sync Status API. See /docs for all methods"}

@app.get("/api_version")
async def api_version():
    return {"version": "0.0.2"}

@app.get("/show_hashtips")
async def show_hashtips():
    return {"version": "0.0.2"}

@app.get("/show_sync_node_data")
async def show_sync_node_data():
    return validation_lib.get_sync_node_data()

@app.get("/chains_monitored")
async def chains_monitored():
    return {"version": "0.0.2"}

@app.get("/nn_balances_report")
async def nn_balances_report():
    with open('/var/www/html/balances_report.json') as f:
        data = json.load(f)
    return data

@app.get("/nn_balances_deltas")
async def nn_balances_deltas():
    with open('/var/www/html/balances_deltas.json') as f:
        data = json.load(f)
    return data

@app.get("/nn_funding")
async def nn_funding():
    with open('/var/www/html/notary_funds.json') as f:
        data = json.load(f)
    return data

@app.get("/chain_sync_stats/{ticker}")
async def chain_sync_stats(ticker: str = "ALL"):
    return {"version": "0.0.2"}

if __name__ == "__main__":
    format = '%(asctime)s %(levelname)-8s %(message)s'
    uvicorn.run(app, host="127.0.0.1", port=8000, forwarded_allow_ips='138.201.207.24')
