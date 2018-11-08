#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

geoipupdate -d $DIR -f $DIR/GeoIP.conf -v
