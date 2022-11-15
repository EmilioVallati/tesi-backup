import sys
import jsonpickle
from os.path import exists

from extended_topology import get_topology
from event_report import Event, EventReport, DamageReport
from utility import ExtendedConfig
EXTENDED_CONFIG = "./extended_conf.ini"

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Invalid Arguments, try: 'python quick_start.py <LATITUDE> <LONGITUDE> <RANGE>'")
        exit()
    # loading configuration file
    if len(sys.argv) == 4:
        print("using default configuration")
        conf_file = EXTENDED_CONFIG
        try:
            if not exists(EXTENDED_CONFIG):
                print("configuration file not detected")
                exit()
            else:
                conf = ExtendedConfig(EXTENDED_CONFIG)
        except Exception:
            print("error reading configuration file")
            exit()

    t = get_topology(conf)
    e = Event(float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]))
    e.print()
    ev_tgt = t.net.get_target_locations(e)
    report = t.process_event(ev_tgt)
    report.print_report()