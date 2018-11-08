#!/bin/bash
pkill -f 'python -u crawl.py crawl.mainnet.conf master'
pkill -f 'python -u crawl.py crawl.mainnet.conf slave'

pkill -f 'python -u ping.py ping.conf master'
pkill -f 'python -u ping.py ping.conf slave'

pkill -f 'python -u resolve.py resolve.conf'
pkill -f 'python -u export.py export.conf'

pkill -f 'python -u api.py'
pkill -f 'python api.py'
