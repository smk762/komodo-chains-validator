import validator_lib

def main():
    while True:
        validator_lib.chains_start_and_sync()
        validator_lib.save_ac_latest_block_data()
        validator_lib.clean_sync_results()

if __name__ == '__main__':
    main()