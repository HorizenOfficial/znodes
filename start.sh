#!/bin/bash
# --- mainnet ---
nohup python -u crawl.py crawl.mainnet.conf master > crawl.mainnet.master.out 2>&1 &

for i in {1..4}
do
nohup python -u crawl.py crawl.mainnet.conf slave > crawl.mainnet.slave.$i.out 2>&1 &
done

#every process creates configurable number of worker threads that keep connections to nodes
nohup python -u ping.py ping.conf master > ping.master.out 2>&1 &

for i in {1..12}
do
nohup python -u ping.py ping.conf slave > ping.slave.$i.out 2>&1 &
done

nohup python -u resolve.py resolve.conf > resolve.out 2>&1 &

nohup python -u export.py export.conf > export.out 2>&1 &

nohup python -u api.py > api.out 2>&1 &

#nohup python -u seeder.py seeder.conf > seeder.out 2>&1 &

#nohup python -u pcap.py pcap.conf > pcap.1.out 2>&1 &
#nohup python -u pcap.py pcap.conf > pcap.2.out 2>&1 &

# --- testnet3 ---
#nohup python -u crawl.py crawl.testnet3.conf master > crawl.testnet3.master.out 2>&1 &

