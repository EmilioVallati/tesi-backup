import sys
from os.path import exists

import graphAnalisys
import network_model as nw
from scenario import Event, get_radius, get_scenario
from utility import Stats, Config
import math

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
    cnt = 0
    statList = []
    #plotting degree distribution only for first and last event
    #total %damage must be collected and measured thorughout the process
    #substituting the single event damage with the total before to make the graph
    print("total events: " + str(len(sc)))

    #preliminary topoloy stat assessment goes here

    #process
    total_internet_damage = 0
    total_population_damage = 0
    #selecting samples before processing events
    samples = net.get_sample()

    for i in sc:
        print("processing event: lat: " + str(i.latitude) + ", lon: " + str(i.longitude) + ", radius: " + str(i.radius))
        t = net.get_targets(i.latitude, i.longitude, i.radius)
        if cnt == 0:
            s = net.get_stats(samples)
            s.internet_damage = float(total_internet_damage)
            s.user_damage = int(total_population_damage)
            graphAnalisys.test_degree_distribution(net.linksList, "start")
            ret = net.process_impact(t, True)
            total_internet_damage += float(ret.internet_damage)
            total_population_damage += int(ret.users_damage)
            statList.append(s)
            cnt += 1
        elif cnt == len(sc)-1:
            ret = net.process_impact(t, True)
            total_internet_damage += float(ret.internet_damage)
            total_population_damage += float(ret.users_damage)
            s = net.get_stats(samples)
            s.internet_damage = float(total_internet_damage)
            s.user_damage = int(total_population_damage)
            statList.append(s)
            graphAnalisys.test_degree_distribution(net.linksList, "end")
            cnt += 1
        else:
            ret = net.process_impact(t, False)
            total_internet_damage += float(ret.internet_damage)
            total_population_damage += int(ret.users_damage)
            #sampling for stats
            if cnt%int(conf.NUMEVENTS) == 0:
                s = net.get_stats(samples)
                s.internet_damage = float(total_internet_damage)
                s.user_damage = int(total_population_damage)
                statList.append(s)
            if cnt%(int(len(sc)/100)) == 0:
                percent = int((cnt/len(sc)*100))
                print("progress: " + str(percent) + "%")
            cnt += 1
    print("total internet % damage: ")
    print(total_internet_damage)
    print("total users disconnectet: ")
    print(total_population_damage)
    #elaborating statistics
    graphAnalisys.plot_stat_variation(statList, "prova")