This repo contains a few scripts for monitoring the chains secured by Komodo's dPoW, to detect and provide an early warning if there is a hash mismatch between participating nodes for specific a block.

A "Sync" node constantly loops through:
- (re)starting a dPoW chain to sync from scratch
- reporting the chain tip block and hash once it is fully sync'd to an oracle
- stopping the chain, and deleting all chain data

Participating nodes each have a custom oracle created on a dedicated smartchain, and periodically report their local block hash of the most recent block reported by the Sync node.

These oracle records are then periodically compared to ensure uniformity between the Sync node and all participating nodes, and:
- a warning is sent via discord or telegram bot messages each hour if a mismatch is detected.
- a status message is set via Discord / Telegram bot every 12 hours if no mismatch is detected.

To participate as a notary node, follow the instructions below:

- Clone this repo - `git clone https://github.com/smk762/komodo-chains-validator/`
- Go to the repo folder - `cd komodo-chains-validator`
- Install pip reqs - `pip3 install -r requirements.txt`
- Start the STATSORCL chain with the following parameters: 
```
komodod -ac_name=STATSORCL -ac_supply=100000000 -ac_reward=10000000000 -ac_staked=99 -ac_cc=762 -ac_halving=762000 -addnode=116.203.120.91 -addnode=116.203.120.163
```
- Import your Notary Node private key - `komodo-cli -ac_name=STATSORCL importprivkey [YOUR_PRIVATE_KEY]`
- Now stop the chain - `komodo-cli -ac_name=STATSORCL stop`
- Then create a file - `nano ~/komodo-chains-validator/config/pubkey.txt` 
- And enter your pubkey (just the pubkey, nothing else),then save the file and exit.
- Last step is to setup a service for the nn_report_hash.py script, so it will restart on reboot, and run in the background.
- Create a file with ` sudo nano /lib/systemd/system/kmd_sync_report.service`, then populate it as below:

```
[Unit]
Description=KMD NN Sync Report Service
After=multi-user.target
Conflicts=getty@tty1.service

[Service]
User=***YOUR USERNAME***
Type=simple
ExecStart=/usr/bin/python3 /***YOUR USERNAME***/komodo-chains-validator/nn_report_hash.py
StandardInput=tty-force
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```
- Start the service with `sudo systemctl start kmd_sync_report.service`
- Check its status with `sudo systemctl status kmd_sync_report.service`
- Set it to run automatically on reboot - `sudo systemctl enable kmd_sync_report.service`
y
