import sys
from os.path import exists
import graphAnalisys
import network_model as nw
from scenario import Event, get_radius, get_scenario
from utility import Stats, Config

SCENARIO_COUNTERVALUE = "./Dataset/countervalue.csv"
SCENARIO_COUNTERFORCE = "./Dataset/counterforce.csv"
DEFAULT_CONFIG = "./default_conf.ini"

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

    net = nw.NetworkModel(conf)
    net.initialize(False)
    sc = get_scenario(SCENARIO_COUNTERVALUE)
    targets = []
    print("building full list of targets")
    for i in sc:
        tgt = net.get_targets(i.latitude, i.longitude, i.radius)
        for t in tgt:
            if t not in targets:
                targets.append(t)
    print("processing full event")
    ret = net.process_impact(targets, True)
    print("total internet % damage: ")
    print(ret.internet_damage)
    print("total users disconnectet: ")
    print(ret.users_damage)

    #elaborating statistics
    sample = net.get_sample()
    stat = net.get_stats(sample)
    print("aspl")
    print(stat.aspl)
    print("components")
    print(stat.disjoint_components)
    print("size of giant component")
    print(stat.size_of_giant_component)
    print("number of nodes")
    print(stat.nodes_number)
    #graphAnalisys.plot_stat_variation(statList, "prova")