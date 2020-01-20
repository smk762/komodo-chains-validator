from lib import validator_lib

def main():
    while True:
        validator_lib.report_nn_tip_hashes()

if __name__ == '__main__':
    import logging
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    main()
