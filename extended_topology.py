import sys
from os.path import exists
import graphAnalisys
import extended_network_model as nw
from utility import ExtendedConfig, copy_location_dict
import networkx as nx
from os.path import exists
import operator
from location import Location
from event_report import Event, EventReport

#initialize and return an ExtendedTopology object and the correspondent ExtendedNetworkModel, using the config file

def get_topology(conf, v=False):
    t = ExtendedTopology()
    t.verbose = v
    t.n_samples = conf.NUMSAMPLES
    t.conf = conf
    # creating topology
    if v:
        print("///////////////////////////////////")
        print("Creating new topology")
    t.net = nw.ExtendedNetworkModel(conf)
    try:
        t.net.initialize(conf.STAGE, v)
    except Exception as e:
        print("ERROR")
        print(e)
        sys.exit()

    if v:
        print("Selecting sample nodes")
    t.samples = t.net.get_samples(t.n_samples)
    if v:
        print(t.samples)
    return t

#returns a copy of an ExtendedTopology object, with the same state of the network, but different sample nodes
#use ExtendedTopology.set_samples(origin.samples) afterwards to use the same samples

def copy_topology(origin):
    if not isinstance(origin, ExtendedTopology):
        print("not an ExtendedTopology")
        raise Exception
    t = ExtendedTopology()
    t.verbose = origin.verbose
    if t.verbose:
        print("creating copy of")
        print(origin)

    t.n_samples = origin.n_samples

    #crerating network copying network dictionaries
    t.net = nw.ExtendedNetworkModel(origin.conf)
    t.net.fac_to_coord = origin.net.fac_to_coord.copy()
    t.net.fac_to_asn = origin.net.fac_to_asn.copy()
    t.net.serviceDict = origin.net.serviceDict.copy()
    t.net.detectableLinks = origin.net.detectableLinks.copy()
    t.net.asn_to_location = copy_location_dict(origin.net.asn_to_location)

    for l in origin.net.linksList:
        t.net.linksList.append(l)
    for a in origin.net.topology_AS:
        t.net.topology_AS.append(a)
    t.net.topology_graph = graphAnalisys.make_graph(t.net.linksList)

    # a copy of a topology selects different samples for statistics
    t.samples = t.net.get_samples(t.n_samples)
    return t


#argument is a list of EventResult, produces measurements on the collective set of independent events
#this method only prints the results
def get_aggregated_result(result_list):
    print("Number of events processed:")
    print(len(result_list))
    miss_cnt = 0
    target_num = []
    damage_list_pop = []
    damage_list_int = []
    for r in result_list:
        if len(r.lost_facilities) == 0:
            miss_cnt += 1
        damage_list_pop.append(r.global_user_loss)
        damage_list_int.append(r.global_internet_loss)
        target_num.append(len(r.lost_facilities))
    print("maximum targets hit")
    print(max(target_num))
    print("number of events that do not hit facilities")
    print(miss_cnt)
    print("average number of facility disconnected")
    tot_t = sum(target_num)
    avg_t = tot_t/len(target_num)
    print(avg_t)
    print("maximum damage sustained:")
    print("users: " + str(max(damage_list_pop)))
    print("internet %: " + str(max(damage_list_int)))
    print("average damage:")
    tot_u = sum(damage_list_pop)
    avg_u = tot_u/len(damage_list_pop)
    tot_i = sum(damage_list_int)
    avg_i = tot_i/len(damage_list_int)
    print("users: " + str(avg_u))
    print("internet %: " + str(avg_i))


class ExtendedTopology:
    def __init__(self):
        self.verbose = False
        self.n_samples = 0
        # creating topology
        self.net = None
        self.samples = []

    #input: list of Location objects to remove
    def process_event(self, t, verbose=False):
        if isinstance(t, Location):
            targets = [t]
        else:
            targets = t
        #initializing report
        report = EventReport()
        report.lost_locations = targets
        if verbose:
            print("lost locations:")
            for r in targets:
                r.print()


        #facilities ID are saved in a single list as well for convenience
        report.lost_facilities = []
        for t in targets:
            if t.facility is not None and t.facility not in report.lost_facilities:
                if verbose:
                    print("facility "+ str(t.facility) + " recognized")
                report.lost_facilities.append(t.facility)
        if verbose:
            print("getting topology starting stats")
        report.starting_locations = self.net.get_num_locations()
        report.starting_AS = len(self.net.asn_to_location)
        report.starting_facilities = self.net.get_num_facilities()
        report.starting_links = len(self.net.linksList)
        report.sample_nodes = self.samples
        report.mode = self.net.mode
        if verbose:
            print("getting graph starting stats")

        #returns Stats object
        start_stat = graphAnalisys.get_stats(self.net.topology_graph, self.samples)

        # number of nodes, giant component size, number of disjoint component, isolated nodes, aspl of sample
        report.graph_nodes_start = start_stat.nodes_number
        report.starting_giant_component = start_stat.size_of_giant_component
        report.starting_disjoint = start_stat.disjoint_components
        report.starting_isolates = start_stat.isolated_nodes
        report.starting_aspl = start_stat.aspl
        report.starting_conn = start_stat.avg_node_connectivity

        if verbose:
            print("///////////////////////////////////////////////////////\n")
            print("processing next event")
            print("target locations")
            for t in targets:
                t.print()
            print("starting links: " + str(len(self.net.linksList)) + "\n")
        #compiles report
        res = self.net.update_topology(targets, self.verbose)
        if verbose:
            print("reporting")
        for l in res.dead_links:
            if l not in report.lost_links:
                report.lost_links.append(l)
        for a in res.dead_AS:
            if a not in report.lost_AS:
                report.lost_AS.append(a)
        if verbose:
            remaining = len(self.net.linksList)
            print("lost links: " + str(len(res.dead_links)) + "\n")
            print(res.dead_links)
            print("remaining links: " + str(remaining) + "\n")
            print("lost AS: " + str(len(res.dead_AS)) + '\n')
            print(res.dead_AS)
        # returns a DamageReport list
        if verbose:
            print("measuring damage")
        dmg = self.net.get_service_damage(res.dead_AS, self.verbose)
        for d in dmg:
            report.damage_list.append(d)

        #calculate total damage from list
        report.get_global_damage()
        if verbose:
            report.print_damage()

        #ending stats
        if verbose:
            print("measuring ending stats")

        #returns Stats object
        ending_stat = graphAnalisys.get_stats(self.net.topology_graph, self.samples)

        report.graph_nodes_end = ending_stat.nodes_number
        report.ending_giant_component = ending_stat.size_of_giant_component
        report.ending_aspl = ending_stat.aspl
        report.ending_conn = ending_stat.avg_node_connectivity
        report.ending_disjoint = ending_stat.disjoint_components
        report.ending_isolates = ending_stat.isolated_nodes

        return report

    #Deletes current sample set and substitutes it with a list
    def set_samples(self, sample_list):
        self.samples = []
        for s in sample_list:
            self.samples.append(s)
