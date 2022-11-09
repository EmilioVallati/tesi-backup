import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from networkx.algorithms import approximation
import random

class Stats:
    def __init__(self):
        self.aspl = 0
        self.avg_node_connectivity = 0
        self.size_of_giant_component = 0
        self.disjoint_components = 0
        self.nodes_number = 0
        self.n_sample = 0
        self.user_damage = 0
        self.internet_damage = 0
        self.isolated_nodes = 0
        self.sample_nodes = []

def make_graph(linkslist):
    g = nx.Graph()
    for e in linkslist:
        g.add_edge(e[0], e[1])
    return g

def update_graph(g, dead_links, dead_as):
    for l in dead_links:
        if (int(l[0]), int(l[1])) in g.edges:
            g.remove_edge(int(l[0]), int(l[1]))
    for a in dead_as:
        if int(a) in g.nodes:
            g.remove_node(int(a))

#takes dictionary of links and facilities, plots topology graph, unfeasible for huge graphs
def plot_topology(graph, file):
    #plt.figure(figsize=(50, 50), dpi=300)
    pos = nx.layout.kamada_kawai_layout(graph)

    #node_sizes = [3 + 10 * i for i in range(len(G))]
    node_size = 1
    M = graph.number_of_edges()
    #edge_colors = range(2, M + 2)
    edge_colors = 2
    #edge_alphas = [(5 + i) / (M + 4) for i in range(M)]
    edge_alphas = 0.5

    #nodes = nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color='blue')
    nodes = nx.draw_networkx_nodes(graph, pos, node_size=0.1, node_color='blue')
    #edges = nx.draw_networkx_edges(G, pos, node_size=node_sizes, arrowstyle='->',
    #                               arrowsize=10, edge_color=edge_colors,
    #                               edge_cmap=plt.cm.Blues, width=2)
    edges = nx.draw_networkx_edges(graph, pos, arrowstyle='->', arrowsize=1, width=0.05)
    # set alpha value for each edge
    #for i in range(M):
    #    edges[i].set_alpha(edge_alphas[i])

    #pc = mpl.collections.PatchCollection(edges, cmap=plt.cm.Blues)
    #pc.set_array(edge_colors)
    #pc = mpl.collections.PatchCollection(edges)
    #plt.colorbar(pc)
    plt.savefig(file, dpi=2000)

# dictionary with links as keys
# plots degree distribution graph
def test_degree_distribution(graph, file):

    #find giant component
    gcc = sorted(nx.connected_components(graph), key=len, reverse=True)
    g0 = graph.subgraph(gcc[0])

    degree_sequence = sorted((d for n, d in graph.degree()), reverse=True)
    d_max = max(degree_sequence)

    degrees = np.arange(1, d_max)
    counter = []
    for i in degrees:
        counter.append(degree_sequence.count(i))
    counter_np = np.array(counter)


    cdf = counter_np.cumsum() / counter_np.sum()
    ccdf = 1 - cdf

    fig = plt.figure("Degree", figsize=(8, 8))
    fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(12, 4))
    #ax1.plot(degrees, cdf, label='cdf')
    ax1.plot(degrees, ccdf, label='ccdf')
    ax1.legend()
    ax1.set_xscale("log")

    ax2.bar(degrees, cdf, label='cdf')
    #ax2.bar(degrees, ccdf, bottom=cdf, label='ccdf')
    ax2.margins(x=0.01)
    ax2.set_xticks(degrees)
    ax2.set_xticklabels([f'{y % 100:02d}' for y in degrees])
    ax2.set_xscale("log")
    ax2.legend()

    plt.tight_layout()
    plt.savefig(file)
    plt.close()

#selecting fixed samples for aspl measurement
def get_sample_from_giant_component(graph, ns):

    #find giant component
    gcc = sorted(nx.connected_components(graph), key=len, reverse=True)
    g0 = graph.subgraph(gcc[0])

    #select ns random link samples (requires 2*ns the nodes)
    samples = random.sample(g0.nodes, int(ns))
    return samples



#single event stats
def get_stats(g, sample, filename=None):
    stat = Stats()

    #find giant component
    gcc = sorted(nx.connected_components(g), key=len, reverse=True)
    g0 = g.subgraph(gcc[0])

    #collecting node numbers
    stat.nodes_number = g.number_of_nodes()
    stat.size_of_giant_component = nx.number_of_nodes(g0)
    stat.disjoint_components = nx.number_connected_components(g)

    #number of isolated nodes
    stat.isolated_nodes = nx.number_of_isolates(g)

    #sampling nodes for aspl and vertex connectivity approx.
    l = int(len(sample)//2)
    stat.n_sample = l
    sampled_src = sample[:l]
    sampled_dest = sample[l:]

    count = 0
    sum_aspl = 0
    flag = False
    for s in sampled_src:
        for d in sampled_dest:
            if s != d:
                try:
                    dist = nx.shortest_path_length(g0, s, d)
                except nx.NodeNotFound:
                    dist = 0
                    flag = True
                count += 1
                sum_aspl += dist
    avg = sum_aspl/count
    if flag is True:
        print("one of the sample nodes was removed")
        stat.aspl = 0
    else:
        stat.aspl = avg



    if filename is not None:
        with open(filename, 'w', encoding="utf-8") as wrF:
            string = ("number of nodes: " + str(stat.nodes_number) + "\n")
            string += ("size of giant component: " + str(stat.size_of_giant_component) + "\n")
            string += ("number of disjoint components: " + str(stat.disjoint_components) + "\n")
            string += ("number of samples: " + str(stat.n_sample) + "\n")
            if flag is True:
                string += ("aspl couldn't be measured, as one of the sample nodes has been removed")
            else:
                string += ("sampled aspl: " + str(stat.aspl) + "\n")
            wrF.write(string)
            wrF.close()
    return stat

#plots variation of values, requires multiple events and list of stats
def plot_stat_variation(statList, filename):
    x = np.array(range(0, len(statList)))
    y_aspl = []
    y_sogc = []
    y_discomp = []
    y_int_damage = []
    y_pop_damage = []
    y_isolates = []
    y_fac = []
    y_links = []
    y_as = []
    for i in statList:
        y_aspl.append(i.aspl)
        y_sogc.append(i.size_of_giant_component)
        y_discomp.append(i.disjoint_components)
        y_int_damage.append(i.internet_damage)
        y_pop_damage.append(i.user_damage)
        y_isolates.append(i.isolates)
        y_fac.append(i.fac_lost)
        y_links.append(i.links_lost)
        y_as.append(i.as_lost)

    #aspl variation plot

    y = np.array(y_aspl)
    plt.plot(x, y)
    plt.savefig(str(filename) + "/aspl_")
    plt.close()

    #size of giant component variation plot

    y = np.array(y_sogc)
    plt.plot(x, y)
    plt.savefig(str(filename) + "/giant_component")
    plt.close()

    #disjoint components variation

    y = np.array(y_discomp)
    plt.plot(x, y)
    plt.savefig(str(filename) + "/disjoin_components")
    plt.close()

    #number of isolates variation
    y = np.array(y_isolates)
    plt.plot(x, y)
    plt.savefig(str(filename) + "/isolates")
    plt.close()

    #total internet damage progression
    y = np.array(y_int_damage)
    plt.plot(x, y)
    plt.savefig(str(filename) + "/damage_internet")
    plt.close()

    #total population service lost
    y = np.array(y_pop_damage)
    plt.plot(x, y)
    plt.savefig(str(filename) + "/damage_population")
    plt.close()

    #facilities lost over time
    y = np.array(y_fac)
    plt.plot(x, y)
    plt.savefig(str(filename) + "/facilities_lost")
    plt.close()

    #as lost over time
    y = np.array(y_as)
    plt.plot(x, y)
    plt.savefig(str(filename) + "/as_lost")
    plt.close()

    #links lost over time
    y = np.array(y_links)
    plt.plot(x, y)
    plt.savefig(str(filename) + "/links_lost")
    plt.close()
