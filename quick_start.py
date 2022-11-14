import sys
import jsonpickle

from extended_topology import get_topology
from event_report import Event, EventReport, DamageReport
from utility import ExtendedConfig
if __name__ == '__main__':
    conf_file = "./extended_conf.ini"
    conf = ExtendedConfig(conf_file)
    t = get_topology(conf, True)
    e = Event(51.5, -0.12, 1)
    ev_tgt = t.net.get_target_locations(e)
    report = t.process_event(ev_tgt, True)

    report.print_report()