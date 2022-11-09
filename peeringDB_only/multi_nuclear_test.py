import sys
from os.path import exists
import graphAnalisys
import network_model as nw
from topology_analyzer import Event, Topology, EventReport, get_topology, copy_topology, get_aggregated_result
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
    t_start = get_topology(conf.NUMSAMPLES, conf.NUMEVENTS, conf.CUSTOMER_FILE, conf.RELFILE, conf.LINKFILE, conf.DBFILE,
                 conf.LOGFILE, conf.MODE, conf.FULL_INIT, False)


    sc = get_scenario(SCENARIO_EUROPE1MIL)
    #plotting degree distribution only for first and last event
    #total %damage must be collected and measured thorughout the process
    #substituting the single event damage with the total before to make the graph
    #making single event
    cnt = 0
    report_list = []
    first_miss = True
    miss_report = EventReport

    for e in sc:
        cnt += 1
        temp = copy_topology(t_start)
        ev_tgt = temp.net.get_targets(float(e.latitude), float(e.longitude), e.radius)
        if len(sc) > 100:
            if cnt % (int(len(sc) / 100)) == 0:
                percent = int((cnt / len(sc) * 100))
                print("progress: " + str(percent) + "%")
        report = EventReport()

        if len(ev_tgt) != 0:
            report = temp.process_event(ev_tgt)
        #process only the first miss then copy the result
        else:
            if first_miss is True:
                miss_report = temp.process_event(ev_tgt)
                first_miss = False
            else:
                report = miss_report

        report_list.append(report)

    print(len(report_list))

    #full analysis
    get_aggregated_result(report_list)

