#Geographical area containing locations to be removed from physical topology

class Event:
    def __init__(self, lat, lon, dist):
        self.latitude = lat
        self.longitude = lon
        self.radius = dist
    def print(self):
        print("Event@(" + str(self.latitude) + ',' + str(self.longitude)+') range: '+str(self.radius))

#Consequences of a list of one or more ASN being removed:
#user_damage (int) number of users no longer connected to the network
#local_percent (float) % of total users of country represented by user_damage
#total_percent (float) % of global Internet users lost

class DamageReport:
    def __init__(self, country, count=0, ud=0, lp=0, tp=0):
        self.cc = country
        self.as_count = count
        self.as_list = []
        self.users_damage = ud
        self.local_percent = lp
        self.total_percent = tp

#mode: 'volatile' or 'stable'
#starting_links, starting_AS, starting_facilities, starting_locations: (int) number of elements in topology before event
#damage_list: list of DamageReport objects
#lost_facilities: list of (int), removed facilities_id. redundant with lost_locations
# useful for easier access to facilities
#lost_locations: list of Location object
#lost_AS: list of (int)
#lost_links: list of (int, int)
#graph_nodes_start, graph_nodes_end: (int) number of nodes in NetworkModel.network_graph before and after event
#starting_giant_component, ending_giant_component: (int) size of Giant Component of NetworkModel.network_graph
#starting_disjoint, ending_disjoint: (int) number of disjoint components of the graph
#starting_isolates, ending_isolates: (int) number of nodes with no neighbors in graph
#sample_nodes: list of (int)
#num_sample: (int) number of sample nodes to take from the graph
#starting_aspl, ending_aspl: (float) Average Shortest Path Length measured between sample nodes
#global_user_lost: (int) call self.get_global_damage() to compute
#global_internet_lost: (float) call self.get_global_damage() to compute

class EventReport:
    def __init__(self):
        self.mode = ""
        self.starting_links = 0
        self.starting_AS = 0
        self.starting_facilities = 0
        self.starting_locations = 0
        self.damage_list = []
        self.lost_facilities = []
        self.lost_locations = []
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
        print("total number of locations where AS were detected")
        print(self.starting_locations)
        print("lost locations:")
        print(len(self.lost_locations))
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

