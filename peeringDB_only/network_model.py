import operator
from os.path import exists
import sqlite3
from sqlite3 import Error
import numpy


import graphAnalisys
import networkx as nx
from utility import get_distance, read_rebuilt_links, read_full_links, Config

from population_dataset_extractor import parse_service

# collects failed links and AS after a facility is removed
class Result:
    def __init__(self):
        self.dead_links = []
        self.dead_AS = []

class DamageReport:
    def __init__(self, country, count=0, ud=0, lp=0, tp=0):
        self.cc = country
        self.as_count = count
        self.as_list = []
        self.users_damage = ud
        self.local_percent = lp
        self.total_percent = tp

class NetworkModel:
    def __init__(self, cf, rf, lf, dbf, logf, mode, full_init, region=None):
        #file names init
        self.cf = cf
        self.rf = rf
        self.lf = lf
        self.dbf = dbf
        self.logf = logf
        self.mode = mode
        self.full_init = full_init
        self.region = region

        self.topology_graph = nx.Graph()

        # key: fac_id (int) {lat (float), long (float), name (str)}
        self.facilityDict = {}

        # key: fac_id (int) {asn_list}
        self.asnDict = {}

        # topology links list (asn1, asn2) (int, int)
        self.linksList = []

        # as customer service dataset
        # key: entry_id : (AS, country code, #users, % of population serviced, % of internet served) (int, str, int, float, float)
        self.serviceDict = {}

        # group of links that can be reproduced in facilities and where they are reproducible
        # key: (src_AS, dest_as) : [fac_id1, fac_id2 ...]
        self.detectableLinks = {}

    def print_dataset_stats(self):
        print("links in topology:")
        print(len(self.linksList))
        print("AS in topology")
        as_in_topology = []
        for l in self.linksList:
            list(l)
            if l[0] not in as_in_topology:
                as_in_topology.append(l[0])
            if l[1] not in as_in_topology:
                as_in_topology.append(l[1])
        print(len(as_in_topology))
        print("entries in service dataset")
        print(len(self.serviceDict))
        print("countries in service dataset")
        country_count = []
        as_in_servicedict = []
        for k in self.serviceDict:
            if self.serviceDict[k][1] not in country_count:
                country_count.append(self.serviceDict[k][1])
            if self.serviceDict[k][0] not in as_in_servicedict:
                as_in_servicedict.append(self.serviceDict[k][0])
        print(len(country_count))
        print("AS in service dataset")
        print(len(as_in_servicedict))
        print("AS from topology present in service dataset")
        as_cnt = 0
        for a in as_in_topology:
            if a in as_in_servicedict:
                as_cnt += 1
        print(len(as_in_topology))
        print("number of facilities in dataset")
        print(len(self.facilityDict))
        print("number of facilities with at least one AS:")
        print(len(self.asnDict))
        print("number of distinct AS in facilities")
        as_in_asndict = []
        for f in self.asnDict:
            for fa in self.asnDict[f]:
                if fa not in as_in_asndict:
                    as_in_asndict.append(f)
        print(len(as_in_asndict))
        print("number of facility AS in topology")
        fac_as_in_top = []
        for s in as_in_asndict:
            if s in as_in_topology:
                fac_as_in_top.append(s)
        print(len(fac_as_in_top))
        print("number of links that can be reconstructed in facilities")
        print(len(self.detectableLinks))
        print("average number of AS per facility")
        as_count_dict = {}
        tot_as = 0
        for f in self.asnDict:
            as_count_dict[f] = len(self.asnDict[f])
            tot_as += len(self.asnDict[f])
        avg_as = tot_as/len(self.asnDict)
        print(avg_as)
        print("top 3 facilities by number of AS (facility, n* of AS)")
        sorted_as_dict = sorted(as_count_dict.items(), key=operator.itemgetter(1), reverse=True)
        print(sorted_as_dict[:3])
        print("number of nodes in the topology graph")
        print(nx.number_of_nodes(self.topology_graph))
        print("average node degree")
        tot_degree = 0
        degree_dict = {}
        for n in self.topology_graph.nodes():
            degree_dict[n] = self.topology_graph.degree[n]
            tot_degree += self.topology_graph.degree[n]
        sorted_degree_dict = sorted(degree_dict.items(), key=operator.itemgetter(1), reverse=True)
        avg = tot_degree/len(degree_dict)
        print(avg)
        print("top 3 AS with the largest number of neighbors (AS, degree)")
        print(sorted_degree_dict[:3])

    # returns facilities within 'size' from center
    def get_targets(self, lat, lon, size):
        targets = []
        for entry in self.facilityDict:
            if get_distance(lat, lon, self.facilityDict[entry][0], self.facilityDict[entry][1]) <= size:
                targets.append(entry)
        return targets

    def get_samples(self, num_samples):
        return graphAnalisys.get_sample_from_giant_component(self.topology_graph, num_samples)

    # returns list of links deleted from topology
    def remove_facility(self, fac_id, logging=False):

        count = 0
        ret = Result()
        if fac_id in self.facilityDict:
            del self.facilityDict[fac_id]

        if fac_id in self.asnDict:
            del self.asnDict[fac_id]
        # searching for the detected links that are reproduced in the removed facility
        for link in self.detectableLinks:
            if fac_id in self.detectableLinks[link]:
                count += 1
                if logging:
                    print(str(fac_id) + " fac_id found for link " + str(link))
                self.detectableLinks[link].remove(fac_id)
                # no more facility for a link means it's dead
                if len(self.detectableLinks[link]) == 0:
                    ret.dead_links.append(link)

        # removing dead links from detectable topology
        new_dead_links = []
        new_dead_AS = []

        for l in ret.dead_links:
            inv_l = (l[1], l[0])
            #removing from detected topology
            if l in self.detectableLinks.keys():
                del self.detectableLinks[l]
            elif inv_l in self.detectableLinks.keys():
                del self.detectableLinks[inv_l]
            # removing from full topology if present
            if l in self.linksList:
                self.linksList.remove(l)
            elif inv_l in self.linksList:
                self.linksList.remove(inv_l)

            # checking if single AS are still available in facilities or in full topology
            ll = list(l)
            # facilities
            f1 = 0
            f2 = 0
            # full topology
            l1 = 0
            l2 = 0
            #looking for other facilities containing src_AS and dest_AS
            for e in self.asnDict:
                if l[0] in self.asnDict[e]:
                    f1 += 1
                if l[1] in self.asnDict[e]:
                    f2 += 1

            # if no facilities are found, we must look into the full topology.
            if logging:
                print("AS " + str(l[0]) + " found in " + str(f1) + " facilities")
                print("AS " + str(l[1]) + " found in " + str(f2) + " facilities")

            # if specified, we can assume full topology links that feature an AS not present in any facility
            # will be removed as well
            if self.mode == "volatile":
                if f1 == 0:
                    if ll[0] not in new_dead_AS:
                        print("AS " + str(l[0]) + " no longer connected!")
                        new_dead_AS.append(ll[0])
                    for entry in self.linksList:
                        ee = list(entry)
                        if ll[0] in ee:
                            new_dead_links.append(entry)
                            self.linksList.remove(entry)
                            # removing from detected topology
                            if entry in self.detectableLinks.keys():
                                del self.detectableLinks[entry]

                if f2 == 0:
                    if ll[1] not in new_dead_AS:
                        print("AS " + str(l[1]) + " no longer connected!")
                        new_dead_AS.append(ll[1])
                    for entry in self.linksList:
                        ee = list(entry)
                        if ll[1] in ee:
                            new_dead_links.append(entry)
                            self.linksList.remove(entry)
                            if entry in self.detectableLinks.keys():
                                del self.detectableLinks[entry]

            # by default we are assuming that un-detectable links are indestructible, therefore if the full
            # topology contains at least one link with the AS, we cannot discard it
            # looking for links in topology containing the AS
            elif self.mode == 'stable':
                for entry in self.linksList:
                    ee = list(entry)
                    if ll[0] in ee:
                        l1 += 1
                    if ll[1] in ee:
                        l2 += 1


                if logging:
                    print("AS " + str(l[0]) + " found in " + str(f1) + " facilities")
                    print("AS " + str(l[0]) + " found in " + str(l1) + " links")
                    print("AS " + str(l[1]) + " found in " + str(f2) + " facilities")
                    print("AS " + str(l[1]) + " found in " + str(l2) + " links")

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
        if len(new_dead_links) != 0:
            for new in new_dead_links:
                ret.dead_links.append(new)
        if len(new_dead_AS) != 0:
            for new in new_dead_AS:
                if new not in ret.dead_AS:
                    ret.dead_AS.append(new)
        return ret

    #removes target facilities and returns list of dead links and AS
    def update_topology(self, targets, logging=False):
        # removing facility
        ret_all = Result()
        long = False
        cnt = 0
        if len(targets) >= 100:
            long = True
        for t in targets:
            if long:
                cnt += 1
                if cnt % (int(len(targets) / 100)) == 0:
                    percent = int((cnt / len(targets) * 100))
                    print("progress: " + str(percent) + "%")

            if logging:
                print("removing facility " + str(t) + "\n")
            ret = self.remove_facility(t)
            # collect dead links for statistics
            for l in ret.dead_links:
                if l not in ret_all.dead_links:
                    ret_all.dead_links.append(l)
            for a in ret.dead_AS:
                if a not in ret_all.dead_AS:
                    ret_all.dead_AS.append(a)

        #updating graph and collecting statistics
        graphAnalisys.update_graph(self.topology_graph, ret_all.dead_links, ret_all.dead_AS)

        return ret_all


    def print_dictionaries(self, filename):
        wrFilename1 = filename + 'facility.txt'
        wrFilename2 = filename + 'facnet.txt'
        wrFilename3 = filename + 'detectable-links.txt'
        wrFilename4 = filename + 'service.txt'
        wrFilename5 = filename + 'total-links.txt'
        with open(wrFilename1, 'w', encoding="utf-8") as wrF:
            for e1 in self.facilityDict:
                wrF.write(str(e1) + ' ' + str(self.facilityDict[e1]) + "\n")
            wrF.close()
        with open(wrFilename2, 'w', encoding="utf-8") as wrF:
            for e2 in self.asnDict:
                wrF.write(str(e2) + ' ' + str(self.asnDict[e2]) + "\n")
            wrF.close()
        with open(wrFilename3, 'w', encoding="utf-8") as wrF:
            for e3 in self.detectableLinks:
                wrF.write(str(e3) + ' ' + str(self.detectableLinks[e3]) + "\n")
            wrF.close()
        with open(wrFilename4, 'w', encoding="utf-8") as wrF:
            for e4 in self.serviceDict:
                wrF.write(str(e4) + ' ' + str(self.serviceDict[e4]) + '\n')
            wrF.close()
        with open(wrFilename5, 'w', encoding="utf-8") as wrF:
            for e5 in self.linksList:
                wrF.write(str(e5))
            wrF.close()

    # populates the asnDict and facilityDict dictionaries
    def populate_facilities(self):
        """ create a database connection to a SQLite database """
        conn = None
        print("getting facilities geographical coordinates from peeringdb...")
        try:
            conn = sqlite3.connect(self.dbf)
            cur = conn.cursor()
            print(self.region)
            if self.region is not None:
                query = "select id, latitude, longitude, name FROM peeringdb_facility where latitude is not NULL and " \
                        "longitude is not NULL and region_continent == '" + str(self.region) + "'"
                print(query)
                cur.execute(query)
            else:
                cur.execute(
                    "SELECT id, latitude, longitude, name FROM peeringdb_facility where latitude is not NULL and "
                    "longitude is not NULL;")
            facilities = cur.fetchall()
            if len(facilities) == 0:
                print("ERROR")



            for fac in facilities:
                self.facilityDict[fac[0]] = [float(fac[1]), float(fac[2]), fac[3]]
            print("facilities found:")
            print(len(self.facilityDict))

            print("building list of facilities per AS using peeringdb database...")
            cur.execute("SELECT DISTINCT local_asn from peeringdb_network_facility;")
            c = cur.fetchall()
            print("number of AS found within peeringdb facilities:")
            print(len(c))
            cur.execute("SELECT local_asn, fac_id from peeringdb_network_facility;")
            asn = cur.fetchall()
            #if a region was specified, we add to the dictionary only facilities for that region
            if self.region is not None:
                for entry in asn:
                    if entry[1] in self.facilityDict.keys():
                        if entry[1] in self.asnDict.keys():
                            self.asnDict[entry[1]].append(entry[0])
                        else:
                            self.asnDict[entry[1]] = [entry[0]]
            else:
                for entry in asn:
                    if entry[1] in self.asnDict.keys():
                        self.asnDict[entry[1]].append(entry[0])
                    else:
                        self.asnDict[entry[1]] = [entry[0]]
            print("number of facilities found within peeringdb with at least one AS:")
            print(len(self.asnDict))

        except Error as e:
            print("error")
            print(e)
        finally:
            if conn:
                conn.close()

    def get_detected_as_num(self):
        ret = []
        for e in self.asnDict:
            for asn in self.asnDict[e]:
                if e not in ret:
                    ret.append(e)
        return len(ret)

    def build_topology_full(self):
        wrFilename3 = self.lf
        # preparing detectable topology
        # intermediate dataset detectableLinks contains only links that can be recreated in facilities present in asnDict
        for link in self.linksList:
            l = list(link)
            key = (int(l[0]), int(l[1]))
            #links are bidirectional, so inverted src, dest count as same key
            inv_key = (int(l[1]), int(l[0]))

            #searching for facilities containing both src, dest AS
            for fac in self.asnDict:
                if l[0] in self.asnDict[fac] and l[1] in self.asnDict[fac]:
                    if key not in self.detectableLinks.keys() and inv_key not in self.detectableLinks.keys():
                        self.detectableLinks[key] = []
                        self.detectableLinks[key].append(fac)
                    elif key in self.detectableLinks.keys():
                        if fac not in self.detectableLinks[key]:
                            self.detectableLinks[key].append(fac)
                    else:
                        if fac not in self.detectableLinks[inv_key]:
                            self.detectableLinks[inv_key].append(fac)
        # saving detectableLinks for faster access in later runs
        print("number of links that can be reproduced inside peeringdb facilities")
        print(len(self.detectableLinks))
        print("saving detectable topology in " + str(wrFilename3))
        with open(wrFilename3, 'w', encoding="utf-8") as wrF:
            for entry in self.detectableLinks:
                string = str(entry)
                for i in self.detectableLinks[entry]:
                    string += "|"
                    string += str(i)
                string += "\n"
                wrF.write(string)
            wrF.close()

    def build_topology_quick(self):
        self.detectableLinks = read_rebuilt_links(self.lf)
        print("number of links read:")
        print(len(self.detectableLinks))

    def initialize(self):
        print("initializing topology...")
        #dictionaries initialization
        #facilityDict and asnDict
        self.populate_facilities()

        #serviceDict
        print("collecting customer service data...")
        self.serviceDict = parse_service(self.cf)
        print("service entries for countries by AS available:")
        print(len(self.serviceDict))

        #list of links and graph initialization
        print("reading link list from " + str(self.rf))
        for l in read_full_links(self.rf):
            self.linksList.append(l)


        print("number of links in full topology:")
        print(len(self.linksList))

        #detectableLinks
        if self.full_init == 'True' or self.region is not None:
            #build topology from full dataset
            print("generating detectable topology from scratch...")
            self.build_topology_full()

        else:
            if exists(self.lf):
                #use preprocessed data from file
                print("reading detectable links from file")
                self.build_topology_quick()
            else:
                print("ERROR, TOPOLOGY FILE NOT FOUND")
                raise Exception

        #creating the graph object
        print("generating topology graph")
        self.topology_graph = graphAnalisys.make_graph(self.linksList)

    # returns a list of reports with the damage for each country resulting from the loss of a list of AS
    def get_service_damage(self, as_list, logging=False):

        ret = []
        # measure the impact of the event on the service
        # AS are not unique and can appear multiple times if they appear in different countries
        entries = []
        for k in self.serviceDict:
            if self.serviceDict[k][0] in as_list:
                entries.append(self.serviceDict[k])
        # for each country code show damage
        countries = {}
        count = {}
        # collecting entries for each cc
        for e in entries:
            if e[1] not in countries.keys():
                countries[e[1]] = [e]
            else:
                countries[e[1]].append(e)
        #total_pop = 0
        #total_internet = 0
        for c in countries:
            local_percent = 0
            local_pop = 0
            local_internet = 0
            count = 0
            asn = []
            for c1 in countries[c]:
                local_pop += c1[2]
                local_percent += c1[3]
                local_internet += c1[4]
                count += 1
                asn.append(c1[0])
            #total_pop += local_pop
            #total_internet += local_internet

            r = DamageReport(str(c), count, local_pop, local_percent, local_internet)
            for a in asn:
                r.as_list.append(a)
            ret.append(r)
            if logging:
                print(
                    "country code: " + str(c) +
                    " service lost for " + str(local_pop) + " users, " + str(local_percent) +
                    "% of national coverage, totaling " + str(local_internet) + "% of global internet infrastructure")

        #ret.users_damage = total_pop
        #ret.internet_damage = total_internet
        return ret

    #returns object containing dead links and dead AS
    def process_impact(self, targets, logging=False):
        starting_links = len(self.linksList)
        if(logging):
            print("starting links: " + str(starting_links) + "\n")

        result = self.update_topology(targets, logging)

        #damage% is always needed for cumulative measurement
        if(logging):
            remaining = len(self.linksList)
            print("lost links: " + str(len(result.dead_links)) + "\n")
            print("remaining links: " + str(remaining) + "\n")

        return result

