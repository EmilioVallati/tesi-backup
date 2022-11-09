from __future__ import division

import itertools
import sqlite3
from sqlite3 import Error
import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx
from itertools import groupby

# population data for AS network
CUSTOMER_FILE = "../Dataset/customers-per-as-measurements.html"

# coordinates and radius of explosion
DISTANCE = 300
CENTER_LAT = 47.112
CENTER_LON = 10.475

# topology dataset
RELFILE = 'Dataset/20220601.as-rel.v6-stable.txt'
LINKFILE = 'links.txt'

# key: fac_id (int) {lat (float), long (float), name (str)}
facilityDict = {}

# key: fac_id (int) {asn_list}
asnDict = {}

# topology (asn1, asn2) (int, int)
linksList = []

# as customer service dataset
# key: entry_id (AS, country code, #users, % of population serviced, % of internet served) (int, str, int, float, float)
serviceDict = {}

# key: (asn1, asn2) {fac_list}
detectableLinks = {}

from utility import get_distance, read_rebuilt_links, read_full_links

from graphAnalisys import test_degree, plot_topology, test_degree_distribution

from population_dataset_extractor import parse_html

# collects failed lins and AS after a facility is removed
class Result:
    def __init__(self):
        self.dead_links = []
        self.dead_AS = []


# returns facilities within 'size' from center
def check_impact(lat, lon, size):
    targets = []
    for entry in facilityDict:
        if get_distance(lat, lon, facilityDict[entry][0], facilityDict[entry][1]) < size:
            targets.append(entry)
    return targets


# prints an evaluation of how much population, internet structure would be affected by a loss of a number of AS
def get_service_damage(dead_as):
    # AS are not unique and can appear multiple times if they appear in different countries
    entries = []
    print(dead_as)
    for e in serviceDict.keys():
        if serviceDict[e][0] in dead_as:
            entries.append(serviceDict[e])
    print("entries")
    # for each country code show damage
    print(len(entries))
    countries = {}
    # collecting entries for each cc
    for entry in entries:
        if entry[1] not in countries.keys():
            countries[entry[1]] = []
        countries[entry[1]].append(entry)
    total_pop = 0
    total_internet = 0
    for c in countries:
        print(c)
        local_percent = 0
        local_pop = 0
        local_internet = 0
        for c1 in countries[c]:
            local_pop += c1[2]
            local_percent += c1[3]
            local_internet += c1[4]
        total_pop += local_pop
        total_internet += local_internet

        print(
            "country code: " + str(c) +
            " service lost for " + str(local_pop) + " users, " + str(local_percent) +
            "% of national coverage, totaling " + str(local_internet) + "% of global internet infrastructure")

    print("total damage: " + str(total_pop) + " users lost service, for " + str(total_internet) + "% of the total internet")


# returns list of links deleted from topology
def remove_facility(fac_id):
    count = 0
    ret = Result()
    if fac_id in asnDict:
        del asnDict[fac_id]
    for link in detectableLinks:
        # print("looking for " + str(fac_id) + " into " + str(detectableLinks[link]))
        if fac_id in detectableLinks[link]:
            count += 1
            # print(str(fac_id) + " fac_id found for link " + str(link))
            detectableLinks[link].remove(fac_id)
            # no more facility for a link means it's dead
            if len(detectableLinks[link]) == 0:
                ret.dead_links.append(link)
    for l in ret.dead_links:
        # removing dead links from detectable list and topology
        del detectableLinks[l]
        # searching if single AS are still available in facilities
        ll = list(l)
        f1 = 0
        f2 = 0
        l1 = 0
        l2 = 0
        for e in asnDict:
            if l[0] in asnDict[e]:
                f1 += 1
            if l[1] in asnDict[e]:
                f2 += 1

        # removing from topology
        if l in linksList:
            linksList.remove(l)

        # looking for links in topology containing the AS
        for entry in linksList:
            ee = list(entry)
            if ll[0] in ee:
                l1 += 1
            if ll[1] in ee:
                l2 += 1

        # print("AS " + str(l[0]) + " found in " + str(f1) + " facilities")
        # print("AS " + str(l[0]) + " found in " + str(l1) + " links")
        # print("AS " + str(l[1]) + " found in " + str(f2) + " facilities")
        # print("AS " + str(l[1]) + " found in " + str(l2) + " links")

        if f1 == 0 and l1 == 0:
            ret.dead_AS.append(l[0])
            print("AS " + str(l[0]) + " no longer connected!")
        if f2 == 0 and l2 == 0:
            ret.dead_AS.append(l[1])
            print("AS " + str(l[1]) + " no longer connected!")

    # if count != 0:
    # print("facility " + str(fac_id) + " removed from " + str(count) + " links\n")
    # if len(deleted_links) == 0:
    # print("no links lost\n")
    # if len(deleted_links) != 0:
    # print(str(len(deleted_links)) + " links lost")
    return ret


def update_topology(targets):
    starting_links = len(linksList)
    dead_links = []
    dead_AS = []
    # removing facility
    for t in targets:
        print("removing facility " + str(t) + "\n")
        ret = remove_facility(t)
        # collect dead links for statistics
        for l in ret.dead_links:
            dead_links.append(l)
        for a in ret.dead_AS:
            dead_AS.append(a)
    remaining = len(linksList)
    print("dead_links")
    print(len(dead_links))
    print("dead_AS")
    print(len(dead_AS))

    # measure the impact of the event on the service
    get_service_damage(dead_AS)
    # rebuilding the topology (for each link remaining we search for a faculty that houses both AS)
    print("starting links: " + str(starting_links) + "\n")
    print("lost links: " + str(len(dead_links)) + "\n")
    print("remaining links: " + str(remaining) + "\n")


def print_dictionaries():
    wrFilename1 = 'facility_post.txt'
    wrFilename2 = 'facnet_post.txt'
    wrFilename3 = 'links_post.txt'
    with open(wrFilename1, 'w', encoding="utf-8") as wrF:
        for entry in facilityDict:
            wrF.write(str(entry) + ' ' + str(facilityDict[entry]) + "\n")
        wrF.close()
    with open(wrFilename2, 'w', encoding="utf-8") as wrF:
        for entry in asnDict:
            wrF.write(str(entry) + ' ' + str(asnDict[entry]) + "\n")
        wrF.close()
    with open(wrFilename3, 'w', encoding="utf-8") as wrF:
        for entry in detectableLinks:
            wrF.write(str(entry) + ' ' + str(detectableLinks[entry]) + "\n")
        wrF.close()


# populates the asnDict and facilityDict dictionaries
def populate_facilities(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    wrFilename1 = 'facility.txt'
    wrFilename2 = 'facnet.txt'
    try:
        with open(wrFilename1, 'w', encoding="utf-8") as wrF:

            conn = sqlite3.connect(db_file)
            cur = conn.cursor()
            cur.execute("SELECT id, latitude, longitude, name FROM peeringdb_facility where latitude is not NULL and "
                        "longitude is not NULL;")
            facilities = cur.fetchall()

            for fac in facilities:
                facilityDict[fac[0]] = [float(fac[1]), float(fac[2]), fac[3]]
                wrF.write(str(fac[0]) + ' ' + str(facilityDict[fac[0]]) + "\n")
            wrF.close()

        with open(wrFilename2, 'w', encoding="utf-8") as wrF:

            cur.execute("SELECT local_asn, fac_id from peeringdb_network_facility;")
            asn = cur.fetchall()

            for entry in asn:
                if entry[1] in asnDict.keys():
                    asnDict[entry[1]].append(entry[0])
                else:
                    asnDict[entry[1]] = [entry[0]]

            for entry in asnDict:
                wrF.write(str(entry) + " " + str(asnDict[entry]) + "\n")
            wrF.close()


    except Error as e:
        print("error")
        print(e)
    finally:
        if conn:
            conn.close()


# populating the detectableLinks dictionary
def build_topology():
    wrFilename3 = LINKFILE
    # preparing topology
    for l in read_full_links(RELFILE):
        linksList.append(l)
    # intermediate dataset detectableLinks contains only links that can be recreated in facilities present in asnDict
    for link in linksList:
        l = list(link)
        key = (int(l[0]), int(l[1]))
        inv_key = (int(l[1]), int(l[0]))
        for fac in asnDict:
            if l[0] in asnDict[fac] and l[1] in asnDict[fac]:
                if key not in detectableLinks.keys() and inv_key not in detectableLinks.keys():
                    detectableLinks[key] = []
                    detectableLinks[key].append(fac)
                elif key in detectableLinks.keys():
                    if fac not in detectableLinks[key]:
                        detectableLinks[key].append(fac)
                else:
                    if fac not in detectableLinks[inv_key]:
                        detectableLinks[inv_key].append(fac)
    # saving detectableLinks for faster access in later runs
    print("saving intermediate dataset for faster access")
    with open(wrFilename3, 'w', encoding="utf-8") as wrF:
        for entry in detectableLinks:
            string = str(entry)
            for i in detectableLinks[entry]:
                string += "|"
                string += str(i)
            string += "\n"
            wrF.write(string)
        wrF.close()


def rebuild_topology():
    for l in read_full_links(RELFILE):
        linksList.append(l)
    print(len(linksList))
    return read_rebuilt_links(LINKFILE)


if __name__ == '__main__':
    print("populating facility dictionaries")
    populate_facilities("../Dataset/peeringdb.sqlite3")
    # getting service dataset from html
    serviceDict = parse_html(CUSTOMER_FILE)
    print("selecting detectable links")
    # build_topology()
    detectableLinks = rebuild_topology()
    print("testing before impact:\n")
    # plot_topology(linksList, "topology-pre.png")
    test_degree_distribution(linksList, "../Results/old/graph-pre.png")
    targets = check_impact(CENTER_LAT, CENTER_LON, DISTANCE)
    print("targets for impact \n")
    print(targets)
    print("updating topology")
    print("linksList")
    print(len(linksList))
    print("detectableLinks")
    print(len(detectableLinks))
    update_topology(targets)
    print("linksList")
    print(len(linksList))
    print("detectableLinks")
    print(len(detectableLinks))
    # plot_topology(linksList, "topology-post.png")
    print("testing after impact:\n")
    test_degree_distribution(linksList, "../Results/old/graph-post.png")
