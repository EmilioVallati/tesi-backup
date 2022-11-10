from extended_topology import ExtendedTopology, get_topology, get_aggregated_result, copy_topology
from extended_network_model import ExtendedNetworkModel
from utility import ExtendedConfig
from ixpdb_handler import Location, check_location
import sys
from os.path import exists
from scenario import get_scenario
import operator

EXTENDED_CONFIG = "./extended_conf.ini"
SCENARIO = "./Dataset/na1mil"

###################### generic scenario test #####################à

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Scenario file expected as argument")
        exit()
    #loading configuration file
    if len(sys.argv) == 2:
        print("using default configuration")
        conf_file = EXTENDED_CONFIG
        scenario = sys.argv[1]
    else:
        conf_file = sys.argv[2]
        scenario = sys.argv[1]
    if not exists(conf_file):
        print("configuration file not found, shutting down")
        exit()
    else:
        try:
            conf = ExtendedConfig(conf_file)
        except Exception:
            print("error reading configuration file")
            exit()
    v = False

    sc = get_scenario(scenario, v)
    t = get_topology(conf, v)


    target_list = []
    cnt = 0
    print("finding targets")
    for e in sc:
        cnt += 1
        ev_tgt = t.net.get_target_locations(e)
        if len(sc) > 100:
            if cnt % (int(len(sc) / 100)) == 0:
                percent = int((cnt / len(sc) * 100))
                print("progress: " + str(percent) + "%")
        for target in ev_tgt:
            if not check_location(target, target_list):
                target_list.append(target)

    print("total targets")
    print(len(target_list))
    print("processing targets")
    report = t.process_event(target_list, v)

    report.print_report()

