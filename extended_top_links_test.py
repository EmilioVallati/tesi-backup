from extended_topology import ExtendedTopology, get_topology, get_aggregated_result, copy_topology
from extended_network_model import ExtendedNetworkModel
from utility import ExtendedConfig
import sys
import sqlite3
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

    fac_list = [34,39,45,58,40,2262,835,46,4360,43]

    conn = None
    print("getting facilities geographical coordinates from peeringdb...")
    try:
        conn = sqlite3.connect(t_start.net.dbf)
        cur = conn.cursor()
        for f in fac_list:
            query = "SELECT * FROM peeringdb_facility where id == " + str(f) + ";"
            cur.execute(query)
            facilities = cur.fetchall()
            if len(facilities) == 0:
                print("ERROR")
            print(facilities)


    except sqlite3.Error as e:
        print("error")
        print(e)
    finally:
        if conn:
            conn.close()

    for f in fac_list:
        print(f)
        print(t_start.net.fac_to_coord[f][2])

    link_count_dict = {}
    for l in t_start.net.detectableLinks:
        for f in t_start.net.detectableLinks[l]:
            if f not in link_count_dict.keys():
                link_count_dict[f] = 1
            else:
                link_count_dict[f] += 1

    print("top 10 facilities by total number of users serviced by their AS (facility, n* of users)")
    sorted_link_dict = sorted(link_count_dict.items(), key=operator.itemgetter(1), reverse=True)
    top_fac = sorted_link_dict[:10]
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