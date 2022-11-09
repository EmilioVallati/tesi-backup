import sys
import multiprocessing
from os.path import exists
import operator
import graphAnalisys
import network_model as nw
import numpy as np
from topology_analyzer import Event, Topology, get_topology, copy_topology, EventReport, get_aggregated_result
from scenario import get_scenario
from utility import Config
import networkx as nx
import matplotlib.pyplot as plt
from scipy import stats
import sqlite3

SCENARIO_COUNTERVALUE = "./Dataset/countervalue.csv"
SCENARIO_COUNTERFORCE = "./Dataset/counterforce.csv"
DEFAULT_CONFIG = "./default_conf.ini"
SEQUENTIAL = True
RESULT_FILE = "results.txt"
REGION = 'North America'

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

    """ create a database connection to a SQLite database """
    conn = None
    print("getting facilities geographical coordinates from peeringdb...")
    try:
        conn = sqlite3.connect(t_start.net.dbf)
        cur = conn.cursor()
        query = "select distinct id FROM peeringdb_facility where region_continent == '" + str(REGION) + "'"
        print("query")
        print(query)
        cur.execute(query)
        tgt = cur.fetchall()

    except sqlite3.Error as e:
        print("error")
        print(e)
    finally:
        if conn:
            conn.close()


    cnt = 1
    report_list = []

    #getting list of regional facilities
    for e in tgt:
        buf = [e[0]]
        print(e[0])
        print("processing event")
        print(str(cnt) + " of " + str(len(tgt)))
        cnt += 1
        temp = copy_topology(t_start)
        report = EventReport()
        report = temp.process_event(buf)
        report_list.append(report)

    #print("getting results")
    #get_aggregated_result(report_list)

    damages = []
    l_AS = []
    l_links = []

    print("plotting graphs")
    #lost links, lost as, user damage
    for r in report_list:
        tot_dmg = 0
        for d in r.damage_list:
            tot_dmg += d.users_damage
        if tot_dmg != 0:
            damages.append(tot_dmg)
        if len(r.lost_AS) != 0:
            l_AS.append(len(r.lost_AS))
        if len(r.lost_links) != 0:
            l_links.append(len(r.lost_links))

    #as plot
    print("lost as per facility")
    l_AS.sort()
    print(l_AS)

    n_bins = 100
    fig, ax = plt.subplots(figsize=(8, 4))

    # plot the cumulative histogram
    n, bins, patches = ax.hist(l_AS, n_bins, density=True, histtype='step',
                               cumulative=True)


    # tidy up the figure
    ax.grid(True)
    ax.legend(loc='right')
    ax.set_title('Europe')
    ax.set_xlabel('AS lost by removing a facility')
    ax.set_ylabel('Likelihood of occurrence')
    fig.tight_layout()
    fig.savefig("facility_AS_distr_eu.png")
    plt.close()


    #link plot
    print("lost links per facility")
    l_links.sort()
    print(l_links)

    n_bins = 100
    fig, ax = plt.subplots(figsize=(8, 4))

    # plot the cumulative histogram
    n, bins, patches = ax.hist(l_links, n_bins, density=True, histtype='step',
                               cumulative=True)

    ax.set_xscale("log")

    # tidy up the figure
    ax.grid(True)
    ax.legend(loc='right')
    ax.set_title('Europe')
    ax.set_xlabel('links lost by removing a facility')
    ax.set_ylabel('Likelihood of occurrence')
    fig.tight_layout()
    fig.savefig("facility_links_distr_eu.png")
    plt.close()

    #damage plot
    print("lost users per facility")
    damages.sort()
    print(damages)

    n_bins = 100
    fig, ax = plt.subplots(figsize=(8, 4))

    # plot the cumulative histogram
    n, bins, patches = ax.hist(damages, n_bins, density=True, histtype='step',
                               cumulative=True)

    ax.set_xscale("log")

    # tidy up the figure
    ax.grid(True)
    ax.legend(loc='right')
    ax.set_title('Europe')
    ax.set_xlabel('users lost by removing a facility')
    ax.set_ylabel('Likelihood of occurrence')
    fig.tight_layout()
    fig.savefig("facility_damage_distr_eu.png")
    plt.close()
