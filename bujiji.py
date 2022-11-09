import sys
import jsonpickle
from location import Location
from extended_topology import get_topology, copy_topology, get_aggregated_result
from event_report import Event, EventReport, DamageReport
from utility import ExtendedConfig
if __name__ == '__main__':
    conf_file = "./extended_conf.ini"
    conf = ExtendedConfig(conf_file)
    t1 = get_topology(conf)
    ev = Event(50.5, -11.7, 300)
    targets = t1.net.get_target_locations(ev)
    for t in targets:
        t.print()
    result = t1.net.process_impact(targets)
    result.print()