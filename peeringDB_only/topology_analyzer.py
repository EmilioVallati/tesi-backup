import sys
import graphAnalisys
from peeringDB_only import network_model as nw

EXTENDED_CONFIG = ".\extended_config.ini"

def get_topology(n_samples, rep_frequency, c_file, r_file, l_file, db_file, log_file, mode, file_stage, v, region=None):
    t = Topology()
    t.verbose = v
    t.n_samples = n_samples
    t.rep_frequency = rep_frequency
    # creating topology
    t.net = nw.NetworkModel(c_file, r_file, l_file, db_file, log_file, mode, file_stage, region)
    try:
        t.net.initialize()
    except Exception:
        sys.exit()

    t.samples = t.net.get_samples(t.n_samples)
    return t

def copy_topology(origin):
    t = Topology()
    t.verbose = origin.verbose
    t.n_samples = origin.n_samples
    t.rep_frequency = origin.rep_frequency
    # creating topology
    t.net = nw.NetworkModel(origin.net.cf, origin.net.rf, origin.net.lf, origin.net.dbf, origin.net.logf,
                            origin.net.mode, origin.net.full_init)
    t.net.facilityDict = origin.net.facilityDict.copy()
    t.net.asnDict = origin.net.asnDict.copy()
    t.net.serviceDict = origin.net.serviceDict.copy()
    t.net.detectableLinks = origin.net.detectableLinks.copy()
    for l in origin.net.linksList:
        t.net.linksList.append(l)
    t.net.topology_graph = graphAnalisys.make_graph(t.net.linksList)
    t.samples = t.net.get_samples(t.n_samples)
    return t


class EventReport:
    def __init__(self):
        self.mode = ""
        self.starting_links = 0
        self.starting_AS = 0
        self.starting_facilities = 0
        self.damage_list = []
        self.lost_facilities = []
        self.lost_AS = []
        self.lost_links = []
        self.graph_nodes_start = 0
        self.graph_nodes_end = 0
        self.starting_giant_component = 0
        self.ending_giant_component = 0
        self.starting_disjoint = 0
        self.ending_disjoint = 0
        self.sample_nodes = []
        self.num_samples = 0
        self.starting_aspl = 0
        self.ending_aspl = 0
        self.starting_isolates = 0
        self.ending_isolates = 0
        self.global_user_loss = 0
        self.global_internet_loss = 0

    def print_report(self):
        print("link mode:")
        print(self.mode)
        print("links contained in the topology")
        print(self.starting_links)
        print("facilities found within database")
        print(self.starting_facilities)
        print("total number of AS in topology (number of nodes in the graph)")
        print(self.graph_nodes_start)
        print("lost facilities:")
        print(len(self.lost_facilities))
        print("lost links:")
        print(len(self.lost_links))
        print("lost AS:")
        print(len(self.lost_AS))
        print("damage recorded")
        self.print_damage()
        print("global user lost")
        print(self.global_user_loss)
        print("global internet loss")
        print(self.global_internet_loss)
        print("ending graph nodes")
        print(self.graph_nodes_end)
        print("lost_nodes")
        print(self.graph_nodes_start - self.graph_nodes_end)
        print("starting size of giant component")
        print(self.starting_giant_component)
        print("ending size of giant component")
        print(self.ending_giant_component)
        print("starting number of disjoint components")
        print(self.starting_disjoint)
        print("ending number of disjoint components")
        print(self.ending_disjoint)
        print("starting number of isolates")
        print(self.starting_isolates)
        print("ending number of isolates")
        print(self.ending_isolates)
        print("number of samples")
        print(len(self.sample_nodes))
        print("sample nodes")
        print(self.sample_nodes)
        print("starting sampled aspl")
        print(self.starting_aspl)
        print("ending sampled aspl")
        print(self.ending_aspl)

    def get_global_damage(self):
        total_pop = 0
        total_internet = 0
        for r in self.damage_list:
            total_pop += r.users_damage
            total_internet += r.total_percent


        # generating global report
        self.global_user_loss = total_pop
        self.global_internet_loss = total_internet

    def print_damage(self):
        for r in self.damage_list:
            print(
                "country code: " + str(r.cc) +
                " service lost for " + str(r.users_damage) + " users, " + str(r.local_percent) +
                "% of national coverage, totaling " + str(r.total_percent) + "% of global internet infrastructure")
        print("total damage: " + str(self.global_user_loss) + " users lost service, for " +
              str(self.global_internet_loss) + "% of the total internet")




#argument is a list of EventResult
def get_aggregated_result(result_list):
    print("Events processed:")
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


class Event:
    def __init__(self, lat, lon, dist):
        self.latitude = lat
        self.longitude = lon
        self.radius = dist

class Topology:
    def __init__(self):
        self.verbose = False
        self.n_samples = 0
        self.rep_frequency = 0
        # creating topology
        self.net = None
        self.samples = []


    #takes facility number list as input
    def process_event(self, targets):
        #generating report at the start
        report = EventReport()
        report.lost_facilities = targets
        report.starting_AS = self.net.get_detected_as_num()
        report.starting_facilities = len(self.net.asnDict)
        report.starting_links = len(self.net.linksList)
        report.sample_nodes = self.samples
        report.mode = self.net.mode

        # number of nodes, giant component size, number of disjoint component, isolated nodes, aspl of sample
        start_stat = graphAnalisys.get_stats(self.net.topology_graph, self.samples)
        report.graph_nodes_start = start_stat.nodes_number
        report.starting_giant_component = start_stat.size_of_giant_component
        report.starting_disjoint = start_stat.disjoint_components
        report.starting_isolates = start_stat.isolated_nodes
        report.starting_aspl = start_stat.aspl
        report.starting_conn = start_stat.avg_node_connectivity

        if self.verbose:
            print("processing next event")
            print("target facilities")
            print(targets)
            print("starting links: " + str(len(self.net.linksList)) + "\n")
        #compiles report
        res = self.net.update_topology(targets, self.verbose)
        for l in res.dead_links:
            report.lost_links.append(res.dead_links)
        for a in res.dead_AS:
            report.lost_AS.append(res.dead_AS)
        if self.verbose:
            remaining = len(self.net.linksList)
            print("lost links: " + str(len(res.dead_links)) + "\n")
            print("remaining links: " + str(remaining) + "\n")
            print("lost AS")
            print(len(res.dead_AS))
        # returns a DamageReport list
        dmg = self.net.get_service_damage(res.dead_AS)
        for d in dmg:
            report.damage_list.append(d)
        #calculate total damage from list
        report.get_global_damage()

        #ending stats
        ending_stat = graphAnalisys.get_stats(self.net.topology_graph, self.samples)
        report.graph_nodes_end = ending_stat.nodes_number
        report.ending_giant_component = ending_stat.size_of_giant_component
        report.ending_aspl = ending_stat.aspl
        report.ending_conn = ending_stat.avg_node_connectivity
        report.ending_disjoint = ending_stat.disjoint_components
        report.ending_isolates = ending_stat.isolated_nodes

        return report

    def set_samples(self, sample_list):
        self.samples = []
        for s in sample_list:
            self.samples.append(s)
