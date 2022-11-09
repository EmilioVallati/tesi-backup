import sys
from os.path import exists
import graphAnalisys
import network_model as nw
from topology_analyzer import Event, Topology, EventReport, get_topology
from scenario import get_scenario
from utility import Config
import networkx as nx

SCENARIO_COUNTERVALUE = "./Dataset/countervalue.csv"
SCENARIO_COUNTERFORCE = "./Dataset/counterforce.csv"
SCENARIO_EUROPE1MIL = "./Dataset/europe1mil"
DEFAULT_CONFIG = "./default_conf.ini"
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

    topology = get_topology(conf.NUMSAMPLES, conf.NUMEVENTS, conf.CUSTOMER_FILE, conf.RELFILE, conf.LINKFILE, conf.DBFILE,
                 conf.LOGFILE, "volatile", conf.FULL_INIT, False)

    samples = [52510, 204943, 208880, 12296, 266539, 57842, 398123, 207489, 46175, 271343, 396414, 60914, 38253, 37011, 397612, 51190, 31537, 44421, 13283, 14058]

    topology.set_samples(samples)

    sc = get_scenario(SCENARIO_COUNTERVALUE)
    #plotting degree distribution only for first and last event
    #total %damage must be collected and measured thorughout the process
    #substituting the single event damage with the total before to make the graph
    #making single event
    target_list = []
    cnt = 0
    for e in sc:
        cnt += 1
        ev_tgt = topology.net.get_targets(e.latitude, e.longitude, e.radius)
        if len(sc) > 100:
            if cnt % (int(len(sc) / 100)) == 0:
                percent = int((cnt / len(sc) * 100))
                print("progress: " + str(percent) + "%")
        for t in ev_tgt:
            if t not in target_list:
                target_list.append(t)
    report = topology.process_event(target_list)

    report.print_report()
    #elaborating statistics
    #graphAnalisys.plot_stat_variation(report.stat_list, "prova")