#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import logging
import codecs

logger = logging.getLogger(__name__)

# DOCS: https://developers.komodoplatform.com/basic-docs/antara/antara-api/oracles.html

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

def wait_confirm(rpc_proxy, txid):
    start_time = time.time()
    mempool = rpc_proxy.getrawmempool()
    while txid in mempool:
        logger.info(colorize("Waiting for "+txid+" confirmation...",'orange'))
        time.sleep(60)
        mempool = rpc_proxy.getrawmempool()
        looptime = time.time() - start_time
        if looptime > 900:
            logger.warning(colorize("Transaction timed out",'red'))
            return False
    logger.info(colorize("Transaction "+txid+" confirmed!",'green'))
    return True

def create_oracle(coin, rpc_proxy, oracle_name, oracle_description, oracletype, datafee=0.001):
    result = rpc_proxy.oraclescreate(str(oracle_name), str(oracle_description), oracletype)
    oracleHex=result['hex']
    oracleResult=result['result']
    while oracleResult != 'success':
        result = rpc_proxy.oraclescreate(str(oracle_name), str(oracle_description), oracletype)
        oracleHex=result['hex']
        oracleResult=result['result']
    oracle_txid = rpc_proxy.sendrawtransaction(oracleHex)
    wait_confirm(rpc_proxy, oracle_txid)
    oraclesList = str(rpc_proxy.oracleslist())
    loop = 0
    while oraclesList.find(oracle_txid) < 0:
        loop += 1
        time.sleep(30)
        oraclesList = str(rpc_proxy.oracleslist())
        logger.info("Waiting for oracle to list, "+str(30*loop)+" sec")
        if loop > 30:
            logger.warning("Oracle didnt list, exiting.")
            sys.exit(0)
    logger.info("Oracle Listing confirmed")
    fund = rpc_proxy.oraclesfund(oracle_txid)
    oracleHex=fund['hex']
    oracleResult=fund['result']
    while oracleResult != 'success':
        fund = rpc_proxy.oraclesfund(oracle_txid)
        oracleHex=fund['hex']
        oracleResult=fund['result']
    fund_txid = rpc_proxy.sendrawtransaction(oracleHex)
    logger.info("Oracle funded")
    wait_confirm(rpc_proxy, fund_txid)
    logger.info("komodo-cli -ac_name="+coin+" oraclesregister "+oracle_txid+" "+str(datafee))
    rego = rpc_proxy.oraclesregister(oracle_txid, str(datafee))
    time.sleep(15)
    oracleHex=rego['hex']
    oracleResult=rego['result']
    while oracleResult != 'success':
        time.sleep(15)
        rego = rpc_proxy.oraclesregister(oracle_txid, str(datafee))
        oracleHex=rego['hex']
        oracleResult=rego['result']
    rego_txid = rpc_proxy.sendrawtransaction(oracleHex)
    wait_confirm(rpc_proxy, rego_txid)
    logger.info("Oracle registered")
    orcl_info = rpc_proxy.oraclesinfo(oracle_txid)
    reg_json=orcl_info['registered']
    while len(reg_json) < 1:
        time.sleep(30)
        orcl_info = rpc_proxy.oraclesinfo(oracle_txid)
        reg_json=orcl_info['registered']
    publisher=str(orcl_info['registered'][0]['publisher'])
    amount = 1000
    sub_list = []
    for i in range (0,10):
        logger.info("Subscribing to oracle ("+str(i)+"/10)")
        result = rpc_proxy.oraclessubscribe(oracle_txid, publisher, str(amount))
        orcl_hex = result['hex']
        sub_txid = rpc_proxy.sendrawtransaction(orcl_hex)
        time.sleep(5)
        sub_list.append(sub_txid)
    pending_subs = len(rpc_proxy.getrawmempool())
    while pending_subs > 0:
        logger.info("Waiting for "+str(pending_subs)+" subscriptions to confirm")
        time.sleep(30)
        pending_subs = len(rpc_proxy.getrawmempool())
    return oracle_txid

def register_oracle(rpc_proxy, oracletxid, datafee=0.001):
    datafee=str(datafee)
    pubkey = rpc_proxy.getinfo()['pubkey']
    rego = rpc_proxy.oraclesregister(oracletxid, datafee)
    if rego['result'] == 'error':
        logger.warning(colorize(rego['error'], 'red'))
        exit(1)
    oracleHex=rego['hex']
    oracleResult=rego['result']
    while oracleResult != 'success':
        rego = rpc_proxy.oraclesregister(oracletxid, datafee)
        oracleHex=rego['hex']
        oracleResult=rego['result']
    regotx = rpc_proxy.sendrawtransaction(oracleHex)
    logger.info(colorize('sending oracle registration tx', 'blue'))
    while len(regotx) != 64:
        time.sleep(15)
        regotx = rpc_proxy.sendrawtransaction(oracleHex)  
        logger.info(colorize('sending oracle registration tx', 'blue'))    
    memPool = str(rpc_proxy.getrawmempool())
    while memPool.find(regotx) < 0:
        time.sleep(5)
        memPool = str(rpc_proxy.getrawmempool())
    orcl_info = rpc_proxy.oraclesinfo(oracletxid)
    reg_json=orcl_info['registered']
    while len(reg_json) < 1:
        logger.info(colorize('waiting for oracle registration', 'blue'))
        time.sleep(15)
        orcl_info = rpc_proxy.oraclesinfo(oracletxid)
        reg_json=orcl_info['registered']
    for reg_pub in reg_json:
        if reg_pub['publisher'] == pubkey:
            publisher=str(reg_pub['publisher'])
            funds=str(reg_pub['funds'])
            logger.info(colorize("publisher ["+publisher+"] registered on oracle ["+oracletxid+"]!", 'green'))
    return publisher

def fund_oracle(rpc_proxy, oracletxid, publisher, funds):
    pubkey = rpc_proxy.getinfo()['pubkey']
    orcl_info = rpc_proxy.oraclesinfo(oracletxid)
    reg_json=orcl_info['registered']
    for reg_pub in reg_json:
        if reg_pub['publisher'] == pubkey:
            exisingFunds=float(reg_pub['funds'])
    amount = float(funds)/10;
    sub_transactions = []
    for x in range(1,11):
        subtx = ''
        while len(subtx) != 64:
            logger.info(colorize("Sending funds "+str(x)+"/10 to oracle", 'blue'))
            subHex = rpc_proxy.oraclessubscribe(oracletxid, publisher, str(amount))['hex']
            subtx = rpc_proxy.sendrawtransaction(subHex)
            time.sleep(5)
        sub_transactions.append(subtx)
        logger.info(colorize("Funds "+str(x)+"/10 sent to oracle", 'blue'))
    while exisingFunds < 1:
        orcl_info = rpc_proxy.oraclesinfo(oracletxid)
        reg_json=orcl_info['registered']
        for reg_pub in reg_json:
            if reg_pub['publisher'] == pubkey:
                exisingFunds=float(reg_pub['funds'])
        logger.info(colorize("waiting for funds to appear on oracle",'blue'))
        time.sleep(15)
    logger.info(colorize("Finished sending "+str(funds)+" to oracle.", 'green'))

def write2oracle(rpc_proxy, oracletxid, message):
    rawhex = codecs.encode(message).hex()
    bytelen = int(len(rawhex) / int(2))
    hexlen = format(bytelen, 'x')
    if bytelen < 16:
        bigend = "000" + str(hexlen)
    elif bytelen < 256:
        bigend = "00" + str(hexlen)
    elif bytelen < 4096:
        bigend = "0" + str(hexlen)
    elif bytelen < 65536:
        bigend = str(hexlen)
    else:
        logger.warning("message too large, must be less than 65536 characters")
    lilend = bigend[2] + bigend[3] + bigend[0] + bigend[1]
    fullhex = lilend + rawhex
    oraclesdata_result = rpc_proxy.oraclesdata(oracletxid, fullhex)
    result = oraclesdata_result['result']
    if result == 'error':
        logger.warning('ERROR:' + oraclesdata_result['error'] + ', try using oraclesregister if you have not already, and check the oracle is funded')
    else:
        rawtx = oraclesdata_result['hex']
        sendrawtransaction_result = rpc_proxy.sendrawtransaction(rawtx)
    logger.info(colorize("Message ["+message+"] written to oracle.", 'green'))
    return sendrawtransaction_result

def read_oracle(rpc_proxy, oracletxid, numrec):
    pubkey = rpc_proxy.getinfo()['pubkey']
    orcl_info = rpc_proxy.oraclesinfo(oracletxid)
    reg_json=orcl_info['registered']
    for reg_pub in reg_json:
        if reg_pub['publisher'] == pubkey:
            batonutxo=reg_pub['baton']
    if 'baton' in locals():
        samples = rpc_proxy.oraclessamples(oracletxid, baton, str(numrec))
        logger.info(colorize("Oracle records retrieved.", 'green'))
        return samples['samples']
    else:
        logger.warning(colorize("ERROR: Oracle batonuto does not exist.", 'red'))

def check_oracleFunds(rpc_proxy, oracletxid, pubkey):
    oraclesinfo = rpc_proxy.oraclesinfo(oracletxid)
    publishers = []
    funds = 0
    timeout = 0
    while funds < 1:
        oraclesinfo = rpc_proxy.oraclesinfo(oracletxid)
        for pub in oraclesinfo['registered']:
            publishers.append(pub['publisher'])
        if pubkey in publishers:
            for pub in oraclesinfo['registered']:
                if pub['publisher'] == pubkey:
                    funds = float(pub['funds'])
        timeout += 1
        if timeout > 12:
            logger.warning("Oracle funding timed out :(")
            sys.exit(1)
        time.sleep(20)
    
def add_oracleFunds(coin, rpc_proxy, oracletxid, pubkey):
    oe_bal = rpc_proxy.getbalance()
    if oe_bal < 100:
        logger.warning(coin+" balance: "+str(oe_bal)+" (need > 100)")
        logger.warning("Your "+coin+" balance needs a top up!")
        logger.warning("Ask @smk762#7640 on Discord to send some.")
        sys.exit(1)
    else:
        logger.info("Adding funds to your "+coin+" subscription...")
        for x in range(10):
            result = rpc_proxy.oraclessubscribe(oracletxid, pubkey, str(10))
            orcl_hex = result['hex']
            rpc_proxy.sendrawtransaction(orcl_hex)

def spawn_oraclefeed(dest_chain, komodod_path, oracle_txid, pubkey, bind_txid):
    oraclefeed_build_log = str(dest_chain)+"_oraclefeed_build.log"
    oraclefeed_build = open(oraclefeed_build_log,'w+')
    subprocess.Popen(["gcc", komodod_path+"/cc/dapps/oraclefeed.c", "-lm", "-o", "oraclefeed"], stdout=oraclefeed_build, stderr=oraclefeed_build, universal_newlines=True)
    oraclefeed_log = str(dest_chain)+"_oraclefeed.log"
    oraclefeed_output = open(oraclefeed_log,'w+')
    subprocess.Popen([komodod_path+"/oraclefeed", dest_chain, oracle_txid, pubkey, "Ihh", bind_txid, komodod_path+"/komodo-cli"], stdout=oraclefeed_output, stderr=oraclefeed_output, universal_newlines=True)
    logger.info(" Use tail -f "+komodod_path+"/"+oraclefeed_build_log+" for oraclefeed build console messages")
    logger.info(" Use tail -f "+komodod_path+"/"+oraclefeed_log+" for oraclefeed log console messages")
