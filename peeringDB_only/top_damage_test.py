import sys
import multiprocessing
from os.path import exists
import operator
from topology_analyzer import get_topology
from utility import Config

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

    print("Number of cpu : ", multiprocessing.cpu_count())

    t_start = get_topology(conf.NUMSAMPLES, conf.NUMEVENTS, conf.CUSTOMER_FILE, conf.RELFILE, conf.LINKFILE, conf.DBFILE,
                 conf.LOGFILE, conf.MODE, conf.FULL_INIT, False)

    damage_count_dict = {}
    for f in t_start.net.serviceDict:
        asnum = t_start.net.serviceDict[f][0]
        users = t_start.net.serviceDict[f][2]
        if asnum not in damage_count_dict.keys():
            damage_count_dict[asnum] = users
        else:
            damage_count_dict[asnum] += users

    print("top 10 AS by number of users serviced (AS, n* of users)")
    sorted_damage_dict = sorted(damage_count_dict.items(), key=operator.itemgetter(1), reverse=True)
    top_as = sorted_damage_dict[:10]
    as_list = []
    for t in top_as:
        as_list.append(t[0])
    print(as_list)
    print("facilities containing the top 10 as")
    targets = []
    for f in t_start.net.asnDict:
        for a in t_start.net.asnDict[f]:
            if a in as_list and f not in targets:
                targets.append(f)

    print(targets)

    report = t_start.process_event(targets)

    report.print_report()