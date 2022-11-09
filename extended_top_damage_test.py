from extended_topology import ExtendedTopology, get_topology, get_aggregated_result, copy_topology
from extended_network_model import ExtendedNetworkModel
from utility import ExtendedConfig
import sys
from os.path import exists
from scenario import get_scenario
import operator
from ixpdb_handler import Location

EXTENDED_CONFIG = ".\extended_conf.ini"
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


    t_start = get_topology(conf, True)

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

    print("facilities containing the top 10 as (fac, n* of AS")
    top_as_fac = {}
    for f in t_start.net.fac_to_asn:
        if f not in top_as_fac.keys():
            top_as_fac[f] = 0
        for a in t_start.net.fac_to_asn[f]:
            if a in as_list:
                top_as_fac[f] += 1
    sorted_fac_dict = sorted(top_as_fac.items(), key=operator.itemgetter(1), reverse=True)
    top_fac = sorted_fac_dict[:10]
    loc_list = []
    for tt in top_fac:
        loc = Location()
        loc.facility = int(tt[0])
        loc_list.append(loc)


    report = t_start.process_event(loc_list, t_start.verbose)

    report.print_report()

