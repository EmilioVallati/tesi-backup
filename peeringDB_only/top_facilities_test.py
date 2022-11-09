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

    t_start = get_topology(conf.NUMSAMPLES, conf.NUMEVENTS, conf.CUSTOMER_FILE, conf.RELFILE,
                           "linksv4_na.txt", conf.DBFILE,
                           conf.LOGFILE, "stable", True, False, "North America")

    user_count_dict = {}
    for f in t_start.net.asnDict:
        user_count_dict[f] = 0
        for a in t_start.net.asnDict[f]:
            if a in t_start.net.serviceDict.keys():
                user_count_dict[f] += t_start.net.serviceDict[a][2]

    print("top 10 facilities by total number of users serviced by their AS (facility, n* of users)")
    sorted_as_dict = sorted(user_count_dict.items(), key=operator.itemgetter(1), reverse=True)
    top_fac = sorted_as_dict[:10]
    tt = []
    for t in top_fac:
        tt.append(t[0])

    print(tt)

    report = t_start.process_event(tt)

    report.print_report()