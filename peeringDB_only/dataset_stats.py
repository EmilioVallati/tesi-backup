import sys
import multiprocessing
from os.path import exists
import graphAnalisys
import network_model as nw
from topology_analyzer import Event, Topology, get_topology, copy_topology
from scenario import get_scenario
from utility import Config
import networkx as nx

SCENARIO_COUNTERVALUE = "./Dataset/countervalue.csv"
SCENARIO_COUNTERFORCE = "./Dataset/counterforce.csv"
DEFAULT_CONFIG = "./default_conf.ini"
SEQUENTIAL = True
RESULT_FILE = "results.txt"

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
            conf = Config(conf_file)
        except Exception:
            print("error reading configuration file")
            exit()


    t_start = get_topology(conf.NUMSAMPLES, conf.NUMEVENTS, conf.CUSTOMER_FILE, conf.RELFILE, conf.LINKFILE, conf.DBFILE,
                 conf.LOGFILE, conf.MODE, conf.FULL_INIT, False)

    t_start.net.print_dataset_stats()
