import sys
import multiprocessing
from os.path import exists
import graphAnalisys
import extended_network_model as nw
from extended_topology import get_topology
from scenario import get_scenario
from utility import ExtendedConfig
import networkx as nx

DEFAULT_CONFIG = "./extended_conf.ini"

if __name__ == '__main__':
    #loading configuration file
    if len(sys.argv) == 1:
        print("using default configuration")
        conf_file = DEFAULT_CONFIG
    else:
        conf_file = sys.argv[1]
    if not exists(conf_file):
        print("configuration file not found, shutting down")
        exit()
    else:
        try:
            conf = ExtendedConfig(conf_file)
        except Exception:
            print("error reading configuration file")
            exit()


    t_start = get_topology(conf, False)

    t_start.net.print_dataset_stats()
