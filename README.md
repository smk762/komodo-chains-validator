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

- Clone this repo `git clone https://github.com/smk762/komodo-chains-validator/`
- Install pip reqs `pip3 install -r requirements.txt`
- Setup a service for the nn_report_hash.py script. First create the file with ` sudo nano /lib/systemd/system/kmd_sync_report.service`, then populate it as below:

```
[Unit]
Description=KMD NN Sync Report Service
After=multi-user.target
Conflicts=getty@tty1.service

[Service]
User=  *** ENTER YOUR USERNAME HERE ***
Type=simple
ExecStart=/usr/bin/python3 /*** USERNAME ***/komodo-chains-validator/nn_report_hash.py
StandardInput=tty-force
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```
- Start the service with `sudo systemctl start kmd_sync_report.service`
- Check its status with `sudo systemctl status kmd_sync_report.service`
- Set it to run automatically on reboot - `sudo systemctl enable kmd_sync_report.service`
