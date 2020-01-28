from lib import validator_lib
import logging
import sys

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%d-%b-%y %H:%M:%S')

fh = logging.FileHandler(sys.path[0]+'/nn_sync_report.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.addHandler(fh)
logger.setLevel(logging.INFO)

def main():
    while True:
        validator_lib.report_nn_tip_hashes()

if __name__ == '__main__':
    main()
