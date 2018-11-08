#!/bin/bash
echo "crawl:master:state: `redis-cli get crawl:master:state`"
echo "crawled nodes cnt: `redis-cli KEYS 'node:*' | wc -l`"
echo "Pending: `redis-cli scard pending`"
echo "Reachable: `redis-cli scard reachable`"
echo "Open: `redis-cli scard open`"
echo "OpenData: `redis-cli scard opendata`"
echo "To resolve: `redis-cli scard toresolve`"
echo "Node map entries: `redis-cli KEYS 'node-map:*' | wc -l`"
