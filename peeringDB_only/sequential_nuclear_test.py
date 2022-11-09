import sys
from os.path import exists
import graphAnalisys
from topology_analyzer import get_topology
from scenario import get_scenario
from utility import Config

SCENARIO_COUNTERVALUE = "./Dataset/countervalue.csv"
SCENARIO_COUNTERFORCE = "./Dataset/counterforce.csv"
DEFAULT_CONFIG = "./default_conf.ini"
RESULT_FILE = "./full_value_sequential"

class Stat:
    def __init__(self):
        self.user_damage = 0
        self.internet_damage = 0
        self.fac_lost = 0
        self.links_lost = 0
        self.as_lost = 0
        self.aspl = 0
        self.size_of_giant_component = 0
        self.disjoint_components = 0
        self.isolates = 0


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
    t = get_topology(conf.NUMSAMPLES, conf.NUMEVENTS, conf.CUSTOMER_FILE, conf.RELFILE, conf.LINKFILE, conf.DBFILE,
                 conf.LOGFILE, conf.MODE, conf.FULL_INIT, True)


    sc = get_scenario(SCENARIO_COUNTERVALUE)
    #plotting degree distribution only for first and last event
    #total %damage must be collected and measured thorughout the process
    #substituting the single event damage with the total before to make the graph
    #making single event
    cnt = 0
    target_list = []
    report_list = []
    sequence_stats = []
    tot_user_damage = 0
    tot_int_damage = 0
    fac_lost_tot = 0
    as_lost_tot = 0
    links_lost_tot = 0

    for e in sc:

        cnt += 1
        ev_tgt = t.net.get_targets(float(e.latitude), float(e.longitude), e.radius)
        target_list.append(ev_tgt)
        if cnt % (int(len(sc) / 100)) == 0:
            percent = int((cnt / len(sc) * 100))
            print("progress: " + str(percent) + "%")
        report = t.process_event(ev_tgt)
        report_list.append(report)
        tot_int_damage += report.global_internet_loss
        tot_user_damage += report.global_user_loss
        as_lost_tot += len(report.lost_AS)
        fac_lost_tot += len(report.lost_facilities)
        links_lost_tot += len(report.lost_links)
        #process only the first miss then copy the result
        #every NUM_EVENTS we collect data on the state of the
        if cnt == 1 or cnt == len(sc) or cnt % int(t.rep_frequency) == 0:
            stat = Stat()
            stat.user_damage = tot_user_damage
            stat.internet_damage = tot_int_damage
            stat.fac_lost = fac_lost_tot
            stat.links_lost = links_lost_tot
            stat.as_lost = as_lost_tot

            if cnt == len(target_list):
                stat.aspl = report.ending_aspl
                stat.size_of_giant_component = report.ending_giant_component
                stat.disjoint_components = report.ending_disjoint
                stat.isolates = report.ending_isolates
            else:
                stat.aspl = report.starting_aspl
                stat.size_of_giant_component = report.starting_giant_component
                stat.disjoint_components = report.starting_disjoint
                stat.isolates = report.starting_isolates
            sequence_stats.append(stat)


    #chart printing
    graphAnalisys.plot_stat_variation(sequence_stats, "../Results")
