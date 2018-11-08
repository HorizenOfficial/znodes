#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# export.py - Exports enumerated data for reachable nodes into a JSON file.
#
# Copyright (c) Addy Yeow Chin Heng <ayeowch@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Exports enumerated data for reachable nodes into a JSON file.
"""

import json
import logging
import os
import redis
import sys
import time
import pycountry
from ConfigParser import ConfigParser
from collections import defaultdict, Counter

# Redis connection setup
REDIS_SOCKET = os.environ.get('REDIS_SOCKET', "/tmp/redis.sock")
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
REDIS_CONN = redis.StrictRedis(unix_socket_path=REDIS_SOCKET,
                               password=REDIS_PASSWORD)

SETTINGS = {}


def get_row(node):
    """
    Returns enumerated row data from Redis for the specified node.
    """
    # address, port, version, user_agent, timestamp, services, is_ssl
    node = eval(node)
    address = node[0]
    port = node[1]
    services = node[-2]

    height = REDIS_CONN.get('height:{}-{}-{}'.format(address, port, services))
    if height is None:
        height = (0,)
    else:
        height = (int(height),)

    hostname = REDIS_CONN.hget('resolve:{}'.format(address), 'hostname')
    hostname = (hostname,)

    geoip = REDIS_CONN.hget('resolve:{}'.format(address), 'geoip')
    if geoip is None:
        # city, country, latitude, longitude, timezone, asn, org
        geoip = (None, None, 0.0, 0.0, None, None, None)
    else:
        geoip = eval(geoip)

    return node + height + hostname + geoip


def get_peers(addr, port, node_lat, node_lng):
    """
    Returns limited list of peers for specified node, excluding peers from same location
    """

    peers = {}
    peer_limit = SETTINGS['export_aggr_peers_max_count']

    map_key = "node-map:{}-{}".format(addr, port)
    node_data_serialized = REDIS_CONN.get(map_key)
    if node_data_serialized is None:
        return []
    node_data = json.loads(node_data_serialized)
    for peer in node_data:
        address = peer['ipv4'] or peer['ipv6'] or peer['onion']
        if not address:
            continue
        geoip = REDIS_CONN.hget('resolve:{}'.format(address), 'geoip')
        if geoip is None:
            continue
        geoip = eval(geoip)
        city = geoip[0]
        lat = geoip[2]
        lng = geoip[3]
        different_location = lat != node_lat or lng != node_lng
        peer_key = '{}|{}'.format(lat, lng)
        if city is not None and different_location and peer_key not in peers:
            peers[peer_key] = {'City': city, 'Latitude': lat, 'Longitude': lng}
        if len(peers) >= peer_limit:
            break

    return list(peers.values())


def export_nodes(nodes, timestamp):
    """
    Merges enumerated data for the specified nodes and exports them into
    timestamp-prefixed JSON file.
    """
    rows = []
    start = time.time()
    for node in nodes:
        row = get_row(node)
        rows.append(row)
    end = time.time()
    elapsed = end - start
    logging.info("Elapsed: %d", elapsed)

    dump = os.path.join(SETTINGS['export_dir'], "{}.json".format(timestamp))
    open(dump, 'w').write(json.dumps(rows, encoding="latin-1"))
    logging.info("Wrote %s", dump)


def export_aggregates(nodes, timestamp):
    """
    Counts aggregates for visualization and exports as JSON
    """
    data = {}
    countries = Counter()
    versions = Counter()
    tls = Counter()
    country_lat_lng = defaultdict(
        lambda: defaultdict(
            lambda: {'City': None, 'Count': 0, 'Latitude': 0, 'Longitude': 0,
                     'Connections': []}
        )
    )

    start = time.time()
    ips = {}
    for node in nodes:
        row = get_row(node)

        # Filtering out same IP addresses
        addr = row[0]
        port = row[1]
        if addr in ips:
            continue
        ips[addr] = 1

        city = row[9]
        try:
            c = pycountry.countries.get(alpha_2=row[10])
            country = c.name
        except KeyError as ke:
            country = 'TOR Node/Unknown'
        
        is_tls = 'tls' if row[6] else 'non-tls'
        zen_ver = row[3].strip('/')
        lat = row[11]
        lng = row[12]
        lat_lng = '{}#{}'.format(lat, lng)

        # Do this only once per location
        if not country_lat_lng[country][lat_lng]['Connections']:
            peers = get_peers(addr, port, lat, lng)
            if peers:
                country_lat_lng[country][lat_lng]['Connections'] = peers

        countries[country] += 1
        versions[zen_ver] += 1
        tls[is_tls] += 1
        country_lat_lng[country][lat_lng]['City'] = city
        country_lat_lng[country][lat_lng]['Count'] += 1
        country_lat_lng[country][lat_lng]['Latitude'] = lat
        country_lat_lng[country][lat_lng]['Longitude'] = lng

    data['Countries'] = dict(countries)
    data['Versions'] = dict(versions)
    data['TLS'] = dict(tls)
    data['CountryLatLng'] = country_lat_lng    

    end = time.time()
    elapsed = end - start
    logging.info("Aggr elapsed: %d", elapsed)

    dump = os.path.join(SETTINGS['export_aggr_dir'], "{}.json".format(timestamp))
    open(dump, 'w').write(json.dumps(data, encoding="latin-1"))


def init_settings(argv):
    """
    Populates SETTINGS with key-value pairs from configuration file.
    """
    conf = ConfigParser()
    conf.read(argv[1])
    SETTINGS['logfile'] = conf.get('export', 'logfile')
    SETTINGS['debug'] = conf.getboolean('export', 'debug')
    SETTINGS['export_dir'] = conf.get('export', 'export_dir')
    if not os.path.exists(SETTINGS['export_dir']):
        os.makedirs(SETTINGS['export_dir'])

    SETTINGS['export_aggr_dir'] = conf.get('export', 'export_aggr_dir')
    if not os.path.exists(SETTINGS['export_aggr_dir']):
        os.makedirs(SETTINGS['export_aggr_dir'])

    SETTINGS['export_aggr_peers_max_count'] = conf.getint(
        'export', 'export_aggr_peers_max_count')


def main(argv):
    if len(argv) < 2 or not os.path.exists(argv[1]):
        print("Usage: export.py [config]")
        return 1

    # Initialize global settings
    init_settings(argv)

    # Initialize logger
    loglevel = logging.INFO
    if SETTINGS['debug']:
        loglevel = logging.DEBUG

    logformat = ("%(asctime)s,%(msecs)05.1f %(levelname)s (%(funcName)s) "
                 "%(message)s")
    logging.basicConfig(level=loglevel,
                        format=logformat,
                        filename=SETTINGS['logfile'],
                        filemode='w')
    print("Writing output to {}, press CTRL+C to terminate..".format(
        SETTINGS['logfile']))

    pubsub = REDIS_CONN.pubsub()
    pubsub.subscribe('resolve')
    while True:
        msg = pubsub.get_message()
        if msg is None:
            time.sleep(0.001)  # 1 ms artificial intrinsic latency.
            continue
        # 'resolve' message is published by resolve.py after resolving hostname
        # and GeoIP data for all reachable nodes.
        if msg['channel'] == 'resolve' and msg['type'] == 'message':
            timestamp = int(msg['data'])  # From ping.py's 'snapshot' message
            logging.info("Timestamp: %d", timestamp)
            nodes = REDIS_CONN.smembers('opendata')
            logging.info("Nodes: %d", len(nodes))
            export_nodes(nodes, timestamp)
            export_aggregates(nodes, timestamp)
            REDIS_CONN.publish('export', timestamp)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
