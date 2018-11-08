Hnodes

Hnodes is currently being developed to estimate the size of the Horizen network (former ZenCash) by finding all the reachable nodes in the network. The current methodology involves sending [getaddr](https://en.bitcoin.it/wiki/Protocol_specification#getaddr) messages recursively to find all the reachable nodes in the network, starting from a set of seed nodes. Live tracking of working nodes is made by keeping active connections. 
Hnodes uses Zcash protocol version 170002 (i.e. >= /MagicBean:1.0.0/), so nodes running an older protocol version will be skipped.

Hnodes utilizes TLS connections. Non TLS connections are possible as fallback.

Hnodes is a fork of ZNodes for Zcash (which is fork of Bitnodes for Bitcoin)
See [Provisioning Bitnodes Network Crawler](https://github.com/ayeowch/bitnodes/wiki/Provisioning-Bitcoin-Network-Crawler) for steps on setting up a machine to run Hnodes. The [Redis Data](https://github.com/ayeowch/bitnodes/wiki/Redis-Data) contains the list of keys and their associated values that are written by the scripts in this project.

