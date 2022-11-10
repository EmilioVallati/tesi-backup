from extended_topology import ExtendedTopology, get_topology, get_aggregated_result, copy_topology
from extended_network_model import ExtendedNetworkModel
from utility import ExtendedConfig
import sys
from os.path import exists
from scenario import get_scenario
import operator
from ixpdb_handler import Location

EXTENDED_CONFIG = "./extended_conf.ini"
SCENARIO_COUNTERVALUE = "./Dataset/countervalue.csv"

if __name__ == '__main__':
    #loading configuration file
    if len(sys.argv) == 1:
        print("using default configuration")
        conf_file = EXTENDED_CONFIG
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

    user_count_dict = {}
    for f in t_start.net.fac_to_asn:
        user_count_dict[f] = 0
        for a in t_start.net.fac_to_asn[f]:
            if str(a) in t_start.net.serviceDict.keys():
                user_count_dict[f] += t_start.net.serviceDict[str(a)][2]

    print("top 10 facilities by total number of users serviced by their AS (facility, n* of users)")
    sorted_as_dict = sorted(user_count_dict.items(), key=operator.itemgetter(1), reverse=True)
    top_fac = sorted_as_dict[:10]
    print(top_fac)
    tt = []
    for t in top_fac:
        l = Location()
        l.facility = int(t[0])
        tt.append(l)

    for l in tt:
        l.print()


    report = t_start.process_event(tt)

    report.print_report()