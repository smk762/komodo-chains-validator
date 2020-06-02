import sys
import time
from lib import validation_lib
import logging
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%d-%b-%y %H:%M:%S')

fh = logging.FileHandler(sys.path[0]+'/looper.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.addHandler(fh)
logger.setLevel(logging.INFO)

def main():
    logger.warning("DONT RUN THIS ON YOUR NOTARY NODE!")
    logger.warning("It will delete assetchain data folders after sync completes...")
    for i in range(10):
        time.sleep(1)
        logger.warning("Use Ctl-C to exit... you have "+str(10-i)+" seconds...")
    while True:
        validation_lib.sim_chains_start_and_sync()

if __name__ == '__main__':
    main()