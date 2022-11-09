import operator
import os.path
from os.path import exists
import sqlite3
from sqlite3 import Error
import numpy
import json
import jsonpickle

import graphAnalisys
import networkx as nx
from utility import get_distance, read_rebuilt_links, read_full_links, get_city_coord, ExtendedConfig
from event_report import DamageReport
from population_dataset_extractor import parse_service
from ixpdb_handler import get_additional_locations
from maxmind_handler import get_geolite_locations
from location import Location, check_location, compare_locations

# collects failed links and AS after a facility is removed
class Result:
    def __init__(self):
        self.dead_links = []
        self.dead_AS = []
    def print(self):
        print("number of removed links:" + str(len(self.dead_links)))
        print(self.dead_links)
        print("number of removed ASes:" + str(len(self.dead_AS)))
        print(self.dead_AS)


#### External file Names #####
#
#IXPDB_ASN_FILE, IXPDB_IXP_FILE, IXPDB_ASN_IXP_FILE: IXPDB dataset tables
#ASN_LIST_FILE: list of ASN in topology used for fast access
#CITY_COORD_FACILITIES, CITY_COORD_ASN: pre-geocoded city geographical coordinates for ASN and Facility locations
#
#FACILITY_COORD_FILE, FACILITY_ASN_FILE, ASN_LOCATION_FILE: stored content of fac_to_coord, fac_to_asn, asn_to_location
#for fast initialization
#CUSTOMER_FILE: service information dataset
#RELFILE: links representing the topology graph
#LINKFILE: stored content of detectableLinks dict
#DBFILE: sqlite3 file of peeringDB dataset
#LOGFILE: general log dump file

class ExtendedNetworkModel:
    def __init__(self, conf):
        #file names init
        self.ixpdbasn = conf.IXPDB_ASN_FILE
        self.ixpdbixp = conf.IXPDB_IXP_FILE
        self.ixpdbs = conf.IXPDB_ASN_IXP_FILE
        self.asnf = conf.ASN_LIST_FILE
        self.ccf = conf.CITY_COORD_FACILITIES
        self.cca = conf.CITY_COORD_ASN
        self.fcf = conf.FACILITY_COORD_FILE
        self.faf = conf.FACILITY_ASN_FILE
        self.alf = conf.ASN_LOCATION_FILE
        self.cf = conf.CUSTOMER_FILE
        self.rf = conf.RELFILE
        self.lf = conf.LINKFILE
        self.dbf = conf.DBFILE
        self.logf = conf.LOGFILE
        self.mode = conf.MODE

        self.topology_graph = nx.Graph()

        # key: fac_id (int) {lat (float), long (float), region (str)}
        self.fac_to_coord = {}

        # key: fac_id (int) {asn_list}
        self.fac_to_asn = {}

        # key: asn_id (int) {Location list}
        self.asn_to_location = {}

        # key: city name (string) {lat, lon} (float, float)
        self.city_to_coord = {}

        # topology links list (asn1, asn2) (int, int)
        self.linksList = []

        # as customer service dataset
        # key: entry_id : (AS, country code, #users, % of population serviced, % of internet served) (int, str, int, float, float)
        self.serviceDict = {}

        # group of links that can be reproduced in facilities and where they are reproducible
        # key: (src_AS, dest_as) : [fac_id1, fac_id2 ...]
        self.detectableLinks = {}

        # list of ASN present in linksList [int, int ...]
        self.topology_AS = []

    #reads list of ASN from file if it exists instead of processing it, useful in case of very large topology
    def get_topology_AS(self, v=False):
        #read from file
        ret = []
        if os.path.exists(self.asnf):
            if v:
                print("reading list of AS in topology from " + str(self.asnf))
            with open(self.asnf, 'r', encoding="utf-8") as f:
                for line in f:
                    ret.append(int(line))
                f.close()
        else:
            if v:
                print("getting list of ASN from topology")
            #otherwise create from 0
            for l in self.linksList:
                if l[0] not in ret:
                    ret.append(l[0])
                if l[1] not in ret:
                    ret.append(l[1])
            #save list
            if v:
                print("saving list of ASN in " + str(self.asnf))
            with open(self.asnf, 'w', encoding="utf-8") as f:
                for a in ret:
                    f.write(str(a))
                    f.write("\n")
                f.close()
        return ret

    #used for debugging and dataset analysis
    def print_dataset_stats(self):
        print("links in topology:")
        print(len(self.linksList))
        print("AS in topology")
        as_in_topology = []
        cnt = 0
        for l in self.linksList:
            cnt += 1
            if cnt % (int(len(self.linksList) / 100)) == 0:
                percent = int((cnt / len(self.linksList) * 100))
                print("progress: " + str(percent) + "%")
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
        print(as_cnt)
        print("number of facilities with coordinates in dataset")
        print(len(self.fac_to_coord))
        print("number of facilities with at least one AS:")
        print(len(self.fac_to_asn))
        print("number of distinct AS in facilities")
        as_in_asndict = []
        for f in self.fac_to_asn:
            for fa in self.fac_to_asn[f]:
                if fa not in as_in_asndict:
                    as_in_asndict.append(int(fa))
        print(len(as_in_asndict))
        print("number of facility AS in topology")
        fac_as_in_top = []
        for s in as_in_asndict:
            if int(s) in as_in_topology:
                fac_as_in_top.append(s)
        print(len(fac_as_in_top))
        print("number of links that can be reconstructed in facilities")
        print(len(self.detectableLinks))
        print("average number of AS per facility")
        as_count_dict = {}
        tot_as = 0
        for f in self.fac_to_asn:
            as_count_dict[f] = len(self.fac_to_asn[f])
            tot_as += len(self.fac_to_asn[f])
        avg_as = tot_as/len(self.fac_to_asn)
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


    #returns list of Location objects
    def get_target_locations(self, event, v=False):
        lat = event.latitude
        lon = event.longitude
        size = event.radius
        if v:
            print("searching targets for (" + str(lat) + "," + str(lon) + ") range: " + str(size))
        targets = []
        #reliability hierarchy for geocoding: facility > city > coordinates
        for entry in self.asn_to_location:
            for loc in self.asn_to_location[entry]:
                #facility
                if loc.facility is not None and loc.facility in self.fac_to_coord.keys():
                    if get_distance(lat, lon, self.fac_to_coord[loc.facility][0], self.fac_to_coord[loc.facility][1]) <= size:
                        if not check_location(loc, targets):
                            if v:
                                st = loc.print()
                                print("target found: " + st)
                            targets.append(loc)
                #city
                elif loc.city is not None and loc.city in self.city_to_coord.keys():
                    if get_distance(lat, lon, self.city_to_coord[loc.city][0], self.city_to_coord[loc.city][1]) <= size:
                        if not check_location(loc, targets):
                            if v:
                                st = loc.print()
                                print("target found: " + st)
                            targets.append(loc)
                #coordinates
                elif loc.coord is not None:
                    if get_distance(lat, lon, float(loc.coord[0]), float(loc.coord[1])) <= size:
                        if not check_location(loc, targets):
                            if v:
                                st = loc.print()
                                print("target found: " + st)
                            targets.append(loc)
        return targets

    #returns a number of randomly selected graph nodes
    def get_samples(self, num_samples):
        return graphAnalisys.get_sample_from_giant_component(self.topology_graph, num_samples)

    def get_num_locations(self):
        cnt = 0
        for a in self.asn_to_location:
            cnt += len(self.asn_to_location[a])
        return cnt

    def get_num_facilities(self):
        ret = []
        for a in self.asn_to_location:
            for loc in self.asn_to_location[a]:
                if loc.facility is not None and loc.facility not in ret:
                    ret.append(loc.facility)
        return len(ret)

##################### EVENT PROCESSING  #############################

    #removes target facilities and returns Result object collecting all removed links and ASN from the targets
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
                if logging and cnt % (int(len(targets) / 100)) == 0:
                    percent = int((cnt / len(targets) * 100))
                    print("progress: " + str(percent) + "%")
            if logging:
                st = str(t.print())
                print("removing location " + st)
            ret = self.remove_location(t, logging)
            # collect dead links for statistics
            if logging:
                print("removal results:")
                print("dead links n*: " + str(len(ret.dead_links)))
            for l in ret.dead_links:
                if logging:
                    print(l)
                if l not in ret_all.dead_links:
                    ret_all.dead_links.append(l)
            if logging:
                print("dead AS n*: " + str(len(ret.dead_AS)))
            for a in ret.dead_AS:
                if logging:
                    print(a)
                if a not in ret_all.dead_AS:
                    ret_all.dead_AS.append(int(a))

        #updating graph and collecting statistics
        if logging:
            print("updating graph")
        graphAnalisys.update_graph(self.topology_graph, ret_all.dead_links, ret_all.dead_AS)
        return ret_all


    # returns a list of reports with the damage for each country resulting from the loss of a list of AS
    # local_pop: number of users lost by a country
    # local_internet: % of users lost over total in country
    # total_internet: % of users lost over total in global Internet
    def get_service_damage(self, as_list, logging=False):
        ret = []
        # measure the impact of the event on the service
        # AS are not unique and can appear multiple times if they appear in different countries
        entries = []
        for k in self.serviceDict:
            if self.serviceDict[k][0] in as_list:
                entries.append(self.serviceDict[k])
        # collecting entries for each country code and showing damage
        countries = {}
        for e in entries:
            if e[1] not in countries.keys():
                countries[e[1]] = [e]
            else:
                countries[e[1]].append(e)
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


    # returns Result object with lists of removed links and ASN
    # if the removed location is a facility, the condition for the loss of an ASN is that
    # it no longer has any facility in its locations list, even if it still contains other locations
    # if it's not a facility, the list must be empty before removing the ASN
    def remove_location(self, removed_loc, logging=False):
        #step 1: removing links detected if input is a facility
        count = 0
        ret = Result()
        if logging:
            print("removing location ")
            removed_loc.print()

        if removed_loc.facility is not None:
            #removing facility from detectableLinks
            fac_id = removed_loc.facility
            if logging:
                print("it's facility " + str(fac_id))
            for link in self.detectableLinks:
                if fac_id in self.detectableLinks[link]:
                    count += 1
                    if logging:
                        print(str(fac_id) + " fac_id found for link " + str(link))
                    self.detectableLinks[link].remove(fac_id)
                    # no more facility for a link means it's dead
                    if len(self.detectableLinks[link]) == 0 and link not in ret.dead_links:
                        if logging:
                            print("link " + str(link) + " has no more facilities")
                        ret.dead_links.append(link)
            if logging:
                print("dead links that were detected in facilities n*: "+ str(len(ret.dead_links)))
            for rl in ret.dead_links:
                if logging:
                    print(rl)
                del self.detectableLinks[rl]

        #step 2: removing location from asn_to_location dict
        for a in self.asn_to_location:
            #ignore ASN not present in topology
            int_a = int(a)
            if int_a in self.topology_AS:
                for loc in self.asn_to_location[a]:
                    if compare_locations(removed_loc, loc):
                        if logging:
                            print("equivalent location for ")
                            removed_loc.print()
                            print("found at AS " + str(a))
                            loc.print()
                            print("removing location")
                            loc.print()
                        self.asn_to_location[a].remove(loc)
                        #if the location removed is a facility and there are no more facilities in the location list
                        #i want to remove the AS regardless of otherlocations
                        if loc.facility is not None:
                            check = False
                            for l in self.asn_to_location[a]:
                                if l.facility is not None:
                                    if logging:
                                        print("AS " + str(a) + " still has at least a facility")
                                    check = True
                                    break
                            if check is False and int_a not in ret.dead_AS:
                                if logging:
                                    print("no more facilities for AS " + str(a))
                                ret.dead_AS.append(int_a)
                        #if the location is not a facility, check for empty list
                        elif len(self.asn_to_location[a]) == 0 and int_a not in ret.dead_AS:
                            if logging:
                                print("no more locations for ASN " + str(a))
                            ret.dead_AS.append(int_a)
        if logging:
            print("deleting entries from asn_to_location")
        for asn in ret.dead_AS:
            if asn not in self.asn_to_location.keys():
                del self.asn_to_location[str(asn)]
            else:
                del self.asn_to_location[asn]
            if int(asn) in self.topology_AS:
                self.topology_AS.remove(int(asn))

        #step 3: removing from the topology links that are no longer mapped in any facility
        new_dead_links = []
        if logging:
            print("removing unmapped links from topology")

        for l in ret.dead_links:
            ll = (int(l[0]), int(l[1]))
            inv_l = (int(l[1]), int(l[0]))
            if ll in self.linksList:
                self.linksList.remove(ll)
            elif inv_l in self.linksList:
                self.linksList.remove(inv_l)

        #step 4: removing links where at least one of the enpoint ASN has been removed
        for a in ret.dead_AS:
            if logging:
                print("consequences for losing AS "+str(a))
            for ll in self.linksList:
                if a == int(ll[0]) or a == int(ll[1]):
                    if ll not in new_dead_links:
                        if logging:
                            print(str(ll) + " lost")
                        new_dead_links.append(ll)
                        self.linksList.remove(ll)
                    #I probably don't need to do this
                    if ll in self.detectableLinks.keys():
                        for f in self.detectableLinks[ll]:
                            self.detectableLinks[ll].remove(f)
                        del self.detectableLinks[ll]
        if logging:
            print("n* lost undetectable links: " + str(len(new_dead_links)))
        for dl in new_dead_links:
            if logging:
                print(dl)
            if dl not in ret.dead_links:
                ret.dead_links.append(dl)
        return ret

####################### DATA PROCESSING FOR INITIALIZATION ###########################

## Based on the stage of the initialization process, certain dictionaries and structures
## must be processed from scratch or may be available as external files

    #converts into Locations data from peeringDB, ixpdb and geoLite2, then saves to file
    def process_asn_locations(self, v=False):
        if v:
            print("getting additional locations from ixpdb")
        # returns dictionary (int) : list of Locations
        self.asn_to_location = get_additional_locations(self.ixpdbasn, self.ixpdbixp, self.ixpdbs)
        if v:
            print("updating facility-asn dict")
        for asn in self.asn_to_location:
            for loc in self.asn_to_location[asn]:
                if loc.facility is not None:
                    if loc.facility not in self.fac_to_asn.keys():
                        self.fac_to_asn[loc.facility] = []
                    if asn not in self.fac_to_asn[loc.facility]:
                        if v:
                            print("adding ASN " + str(asn) + " to facility " + str(loc.facility))
                        self.fac_to_asn[loc.facility].append(asn)
        if v:
            print("current facilities with at least an ASN")
            print(len(self.fac_to_asn))

        if v:
            print("ASN found within ixpd dataset")
            print(len(self.asn_to_location))
            print("total number of locations")
            sum = 0
            for a in self.asn_to_location:
                sum += len(self.asn_to_location[a])
            print(sum)
        #convert facilities in fac_to_asn to Locations to add to asn_to_location
        if v:
            print("building locations from peeringdb data")
        for fac in self.fac_to_asn:
            for asn in self.fac_to_asn[fac]:
                location = Location()
                location.facility = fac
                if asn not in self.asn_to_location.keys():
                    self.asn_to_location[asn] = []
                    if v:
                        print("adding facility " + str(fac) + " to locations for ASN " + str(asn))
                    self.asn_to_location[asn].append(location)
                # check if facility was already found
                elif not check_location(location, self.asn_to_location[asn]):
                    if v:
                        print("adding  facility" + str(fac) + " to locations for ASN " + str(asn))
                    self.asn_to_location[asn].append(location)
        if v:
            print("ASN with at least one location after peeringdb extension")
            print(len(self.asn_to_location))
            print("total locations")
            sum = 0
            for a in self.asn_to_location:
                sum += len(self.asn_to_location[a])
            print(sum)
            print("getting additional locations from maxmind geolite2")

        # returns dictionary (int) : list of Locations
        more_asn = get_geolite_locations()

        if v:
            print("asn found with geolite2")
            print(len(more_asn))
            print("locations found")
            sum = 0
            for a in more_asn:
                sum += len(more_asn[a])
            print(sum)
        #only those AS that do not appear already
        for a in more_asn:
            if a not in self.asn_to_location.keys():
                self.asn_to_location[a] = []
                for l in more_asn[a]:
                    if v:
                        st = l.print()
                        print("adding Location " + st + " to locations for ASN " + str(a))
                    self.asn_to_location[a].append(l)

        if v:
            print("total distinct ASN")
            print(len(self.asn_to_location))
            print("total number of locations")
            sum = 0
            for a in self.asn_to_location:
                sum += len(self.asn_to_location[a])
            print(sum)

        #saving final asn to location dict
        if v:
            print("saving ASN locations in " + str(self.alf))

        with open(self.alf, 'w', encoding='utf-8') as f:
            f.write(jsonpickle.encode(self.asn_to_location))
            f.close()
        if v:
            print("done")

        # city coords are geocoded and build additional Locations
        if v:
            print("retrieving coordinates for city locations for future use")
        city_list = []
        for a in self.asn_to_location:
            for loc in self.asn_to_location[a]:
                if loc.city is not None and loc.city not in city_list:
                    city_list.append(loc.city)

        # either read from file or asks a geocoding provider
        self.city_to_coord = get_city_coord(city_list, self.cca, v)

    #builds fac_to_coord and uses the city of the facility to find coordinates for the ones without a coordinate entry
    def process_facilities_coord(self, v=False):
        #getting facilities coord from peeringDB
        """ create a database connection to a SQLite database """
        conn = None
        if v:
            print("getting facilities geographical coordinates from peeringdb...")
        try:
            conn = sqlite3.connect(self.dbf)
            cur = conn.cursor()
            cur.execute(
                "SELECT id, latitude, longitude, region_continent FROM peeringdb_facility where latitude is not NULL and "
                "longitude is not NULL;")
            facilities = cur.fetchall()
            if len(facilities) == 0:
                print("ERROR")

            for fac in facilities:
                if v:
                    print("facility " + str(fac[0]) + " found at: (" + str(fac[1]) + ',' + str(fac[2]) + ") " + str(fac[3]))
                self.fac_to_coord[int(fac[0])] = [float(fac[1]), float(fac[2]), fac[3]]
            if v:
                print("facilities with directly assigned coordinates found:")
                print(len(self.fac_to_coord))


            #INTEGRATING ADDITIONAL FACILITIES ASSIGNING CITY COORDINATES
            cur.execute("SELECT id, city, region_continent FROM peeringdb_facility where latitude is NULL and "
                    "longitude is NULL and city is not NULL")
            fac_to_city = cur.fetchall()
            #getting coordinates for the cities
            if v:
                print("facilities with only city specified")
                print(len(fac_to_city))
            city_list = []
            for f in fac_to_city:
                if f[1] not in city_list:
                    city_list.append(f[1])

            if v:
                print("getting coordinates for cities")
            city_to_coord = get_city_coord(city_list, self.ccf)

            for ff in fac_to_city:
                if int(ff[0]) not in self.fac_to_coord.keys() and ff[1] in city_to_coord.keys():
                    self.fac_to_coord[int(ff[0])] = [float(city_to_coord[ff[1]][0]), float(city_to_coord[ff[1]][1]), ff[2]]
            if v:
                print("total facilities with coordinates after city integration")
                print(len(self.fac_to_coord))

        except Error as e:
            print("error")
            print(e)
        finally:
            if conn:
                conn.close()

        if v:
            print("saving facility coordinates in " + str(self.fcf))
        with open(self.fcf, 'w', encoding="utf-8") as wrF:
            for entry in self.fac_to_coord:
                c = 0
                string = str(entry)
                string += ":"
                for i in self.fac_to_coord[entry]:
                    c += 1
                    string += str(i)
                    if c != len(self.fac_to_coord[entry]):
                        string += ','
                string += "\n"
                wrF.write(string)
            wrF.close()


    #builds fac_to_asn dictionary
    def process_asn_fac(self, v=False):
        if v:
            print("getting list of ASN in topology")
        #first search for as contained in the facilities
        conn = None
        try:
            conn = sqlite3.connect(self.dbf)
            cur = conn.cursor()
            if v:
                print("building list of facilities per AS using peeringdb database...")
            cur.execute("SELECT DISTINCT local_asn from peeringdb_network_facility;")
            c = cur.fetchall()
            if v:
                print("number of AS found within peeringdb facilities:")
                print(len(c))
            cur.execute("SELECT local_asn, fac_id from peeringdb_network_facility;")
            asn = cur.fetchall()
            for entry in asn:
                if int(entry[1]) in self.fac_to_asn.keys():
                    if int(entry[0]) not in self.fac_to_asn[int(entry[1])]:
                        if v:
                            print("ASN " + str(entry[0]) + " found for facility " + str(entry(1)))
                        self.fac_to_asn[int(entry[1])].append(int(entry[0]))
                else:
                    if v:
                        print("ASN " + str(entry[0]) + " found for facility " + str(entry(1)))
                    self.fac_to_asn[int(entry[1])] = [int(entry[0])]
            if v:
                print("number of facilities found within peeringdb with at least one AS:")
                print(len(self.fac_to_asn))

        except Error as e:
            print("error")
            print(e)
        finally:
            if conn:
                conn.close()

        #saving dictionaries to file
        if v:
            print("saving AS contained in facilities in " + str(self.faf))
        with open(self.faf, 'w', encoding="utf-8") as wrF:
            for entry in self.fac_to_asn:
                c = 0
                string = str(entry)
                string += ":"
                for i in self.fac_to_asn[entry]:
                    c += 1
                    string += str(i)
                    if c != len(self.fac_to_asn[entry]):
                        string += ','
                string += "\n"
                wrF.write(string)
            wrF.close()


    #builds detectableLinks dictionary
    def detect_topology(self, v=False):
        if v:
            print("updating fac_to_asn with data from asn_to_location")
        for k in self.asn_to_location:
            for l in self.asn_to_location[k]:
                if l.facility is not None:
                    if l.facility not in self.fac_to_asn.keys():
                        if v:
                            print("adding ASN " + str(k) + " to facility " + str(l.facility))
                        self.fac_to_asn[l.facility] = []
                    elif k not in self.fac_to_asn[l.facility]:
                        if v:
                            print("adding ASN " + str(k) + " to facility " + str(l.facility))
                        self.fac_to_asn[l.facility].append(k)

        # preparing detectable topology
        # intermediate dataset detectableLinks contains only links that can be recreated in facilities present in asnDict
        if v:
            print("mapping links to facilities")
        cnt = 0
        for l in self.linksList:
            cnt += 1
            if v and cnt % (int(len(self.linksList) / 100)) == 0:
                percent = int((cnt / len(self.linksList) * 100))
                print("progress: " + str(percent) + "%")
            key = (l[0], l[1])
            # links are bidirectional, so inverted src, dest count as same key
            inv_key = (l[1], l[0])

            if v:
                print("link: " + str(key))
            if l[0] in self.asn_to_location.keys() and l[1] in self.asn_to_location.keys():
                #in the list of locations look for the same facility
                for l1 in self.asn_to_location[l[0]]:
                    if l1.facility is not None:
                        for l2 in self.asn_to_location[l[1]]:
                            if l2.facility is not None and l2.facility == l1.facility:
                                #mapping link to facility
                                if key not in self.detectableLinks.keys() and inv_key not in self.detectableLinks.keys():
                                    if v:
                                        print("facility " + str(l1.facility) + " foound for link " + str(key))
                                    self.detectableLinks[key] = []
                                    self.detectableLinks[key].append(l1.facility)
                                elif key in self.detectableLinks.keys():
                                    if l1.facility not in self.detectableLinks[key]:
                                        if v:
                                            print("facility " + str(l1.facility) + " foound for link " + str(key))
                                        self.detectableLinks[key].append(l1.facility)
                                else:
                                    if l1.facility not in self.detectableLinks[inv_key]:
                                        if v:
                                            print("facility " + str(l1.facility) + " foound for link " + str(inv_key))
                                        self.detectableLinks[inv_key].append(l1.facility)
            elif v:
                if l[0] not in self.asn_to_location.keys():
                    print(str(l[0]) + " has no location")
                if l[1] in self.asn_to_location.keys():
                    print(str(l[1]) + " has no location")

        # saving detectableLinks for faster access in later runs
        if v:
            print("number of links that can be reproduced inside peeringdb facilities")
            print(len(self.detectableLinks))
            print("saving detectable topology in " + str(self.lf))
        with open(self.lf, 'w', encoding="utf-8") as wrF:
            for entry in self.detectableLinks:
                string = str(entry)
                for i in self.detectableLinks[entry]:
                    string += "|"
                    string += str(i)
                string += "\n"
                wrF.write(string)
            wrF.close()

        #updating fac_to_asn file
        if v:
            print("updating " + str(self.faf))
        with open(self.faf, 'w', encoding="utf-8") as wrF:
            for entry in self.fac_to_asn:
                c = 0
                string = str(entry)
                string += ":"
                for i in self.fac_to_asn[entry]:
                    c += 1
                    string += str(i)
                    if c != len(self.fac_to_asn[entry]):
                        string += ','
                string += "\n"
                wrF.write(string)
            wrF.close()

####### METHODS TO RECOVER PREPROCESSED DATA FROM FILES #######

    def read_detected_topology(self, v=False):
        if v:
            print("reading detected links from " + str(self.lf))
        self.detectableLinks = read_rebuilt_links(self.lf)
        if v:
            print("number of links read:")
            print(len(self.detectableLinks))

    def read_asn_fac(self, v=False):
        if v:
            print("reading facility ASN from " + str(self.faf))
        if os.path.exists(self.faf):
            with open(self.faf, 'r', encoding="utf-8") as f:
                for line in f:
                    line = line[:-1]
                    l = line.split(':')
                    fac = int(l[0])
                    asn = l[1].split(',')
                    self.fac_to_asn[fac] = []
                    for a in asn:
                        if v:
                            print("ASN " + str(a) + " found for facility " + str(fac))
                        self.fac_to_asn[fac].append(int(a))
                f.close()
        else:
            print(str(self.faf) + " does not exist, try again or select an earlier stage to generate it")
            exit()

    def read_asn_locations(self, v=False):
        #reading asn locations from json
        if v:
            print("reading asn locations from " + str(self.alf))
        with open(self.alf, 'r', encoding='utf-8') as f:
            self.asn_to_location = jsonpickle.decode(f.read())
            f.close()

    def read_facilities_coord(self, v=False):
        if v:
            print("reading facility coordinates from " + str(self.fcf))
        if os.path.exists(self.fcf):
            with open(self.fcf, 'r', encoding="utf-8") as f:
                for line in f:
                    #fac_id:lat,lon,region
                    l = line.split(':')
                    fac = int(l[0])
                    data = l[1].split(',')
                    coord = (float(data[0]), float(data[1]), data[2])
                    if v:
                        print('(' + str(data[0]) + ',' + str(data[1]) + ") " + str(data[2]) +
                              "coordinates found for facility " + str(fac))
                    self.fac_to_coord[fac] = coord
                f.close()
        else:
            print(str(self.fcf) + " does not exist, try again or select an earlier stage to generate it")
            exit()

#############################

    #stage defines which datasets have already been processed and are available in file format
    def initialize(self, stage, verbose=False):
        if verbose:
            print("initializing topology...")
        #list of links and graph initialization
        self.linksList = read_full_links(self.rf, verbose)

        self.topology_AS = self.get_topology_AS()
        if verbose:
            print("generating topology graph")
        self.topology_graph = graphAnalisys.make_graph(self.linksList)

        # serviceDict
        if verbose:
            print("collecting customer service data...")
        self.serviceDict = parse_service(self.cf)
        if verbose:
            print("service entries for countries by AS available:")
            print(len(self.serviceDict))

        #dictionaries initialization
        #phases: facility to coord mapping -> AS to facility mapping -> AS to coordinate mapping -> links to facility mapping
        # facilityDict and asnDict
        file_fac = True
        file_asn_fac = True
        file_asn_loc = True
        file_detected_topology = True
        if verbose:
            print("initialization state selected")
            print(stage)
        #START means nothing is already available as file, everything must be integrated from start
        if stage == "START":
            file_fac = False
            file_asn_fac = False
            file_asn_loc = False
            file_detected_topology = False
        elif stage == "ASN_MAPPING":
            file_fac = True
            file_asn_fac = False
            file_asn_loc = False
            file_detected_topology = False
        elif stage == "LOCATION_MAPPING":
            file_fac = True
            file_asn_fac = True
            file_asn_loc = False
            file_detected_topology = False
        elif stage == "LINK_DETECTION":
            file_fac = True
            file_asn_fac = True
            file_asn_loc = True
            file_detected_topology = False
        elif stage == "DONE":
            file_fac = True
            file_asn_fac = True
            file_asn_loc = True
            file_detected_topology = True

        #now we either read from file or make from scratch the dictionaries
        #fac_to_coord
        if file_fac:
            self.read_facilities_coord()
        else:
            self.process_facilities_coord()
        #fac_to_asn
        if file_asn_fac:
            self.read_asn_fac()
        else:
            self.process_asn_fac()
        #asn_to_coord via router location with maxmind and asn_to_location update, also city_to_coord for city locations
        if file_asn_loc:
            self.read_asn_locations()
            city_list = []
            for a in self.asn_to_location:
                for loc in self.asn_to_location[a]:
                    if loc.city is not None and loc.city not in city_list:
                        city_list.append(loc.city)
            self.city_to_coord = get_city_coord(city_list, self.cca)
        else:
            self.process_asn_locations()
        #detected Links
        if file_detected_topology:
            self.read_detected_topology()
        else:
            self.detect_topology()




