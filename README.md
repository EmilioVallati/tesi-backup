# tesi-vallati
# TIDE

TIDE is a Python tool for network topology modeling and large scale disruption simulation.

              
# Installation

clone using git bash and export files

```
git clone https://github.com/EmilioVallati/tesi-vallati.git
```

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install requirements before running.

```
pip install -r requirements.txt
```

Download the GeoLite2 City: CSV Format dataset from the MaxMind website and extract the files in the 'Dataset' directory
Instructions can be found at https://dev.maxmind.com/geoip/geolite2-free-geolocation-data?lang=en

# Configuration 


configuration file must provide:
### ixpdb dataset files
IXPDB_ASN_FILE, IXPDB_IXP_FILE, IXPDB_ASN_IXP_FILE
### population data for AS network
CUSTOMER_FILE
### topology links
RELFILE
### peeringdb facility db
DBFILE
### log file
LOGFILE
### mapped topology file
LINKFILE
### files where preprocessed data is saved to and loaded from
CITY_COORD_FACILITIES, CITY_COORD_ASN, FACILITY_COORD_FILE,
FACILITY_ASN_FILE, ASN_LOCATION_FILE, ASN_LIST_FILE
### number of samples for average measurements
NUMSAMPLES
### stable or volatile mode (stable mode not implemented for extended source datasets)
MODE
### initialization state (START, ASN_MAPPING, LOCATION_MAPPING, LINK_DETECTION, DONE)
STAGE

               
# SCENARIO FILE 

Input file containing events to process must be a .csv with format
```
Latitude,Longitude,Name,Description,Yield (kt),HOB (m)
```
example:
```
19.432608,-99.133209,MEXICO CITY,,800,1690
```
'Name' and 'Description' fields may be empty

The Dataset folder contains several precompiled scenario files:
'europe1mil'
'na1mil'

             
# QUICK START

A single event can be analyzed using quick_start.py by specifying latitude, longitude and range of the event.
For example:
```
> python quick_start.py 51.5, -0.12, 1
```
will output
```
using default configuration
Event@(51.5,-0.12) range: 1
link mode:
volatile
links contained in the topology
461889
facilities found within database
3474
total number of AS in topology (number of nodes in the graph)
74145
total number of locations where AS were detected
172901
lost locations:
10
lost facilities:
8
lost links:
3717
lost AS:
514
damage recorded
country code: GB service lost for 1754779 users, 2.6599999999999997% of national coverage, totaling 0.04150000000000001% of global internet infrastructure
country code: AT service lost for 17073 users, 0.2% of national coverage, totaling 0.0004% of global internet infrastructure
country code: CN service lost for 12108 users, 0.0% of national coverage, totaling 0.0003% of global internet infrastructure
country code: TZ service lost for 11604 users, 0.09% of national coverage, totaling 0.0003% of global internet infrastructure
country code: NO service lost for 4115 users, 0.08% of national coverage, totaling 0.0001% of global internet infrastructure
country code: SE service lost for 1672 users, 0.02% of national coverage, totaling 0.0% of global internet infrastructure
country code: FK service lost for 358 users, 10.37% of national coverage, totaling 0.0% of global internet infrastructure
total damage: 1801709 users lost service, for 0.04260000000000001% of the total internet
global user lost
1801709
global internet loss
0.04260000000000001
ending graph nodes
73631
lost_nodes
514
starting size of giant component
74145
ending size of giant component
73619
starting number of disjoint components
1
ending number of disjoint components
13
starting number of isolates
0
ending number of isolates
12
number of samples
20
sample nodes
[20118, 30239, 42213, 23089, 133835, 398995, 207325, 49740, 58375, 270531, 264734, 135490, 138206, 28397, 19630, 397695, 262533, 33692, 397690, 270633]
starting sampled aspl
3.67
ending sampled aspl
3.67
```

additionally, the extended_test.py script can be used to perform an analysis on a full scenario

```
python extended_test.py SCENARIO-FILE CONFIGURATION-FILE
```

# Location Usage 

 Locations are points where ASN are detected either within a facility or a single geographical point
 Can have info on Facility ID, City and Coordinates

```
from location import Location, compare_locations
---
loc1 = Location(22, "London", None)
loc1.print()
```

### Output

```
{22,London,None}
```

Two Locations are considered equivalent if their first non-empty field match
```
loc1 = Location(22, "London", None)
loc2 = Location(22, "Paris", (50.5, -11))
compare_locations(loc1, loc2)
```
Returns 'True'

# ExtendedTopology Usage 

```
from extended_topology import get_topology
from utility import ExtendedConfig

# returns ExtendedTopology object
conf = ExtendedConf(CONF_FILE)
foo = get_topology(conf, verbose=False)

# returns copy of 'original' ExtendedTopology object, with different node samples
new_obj = copy_topology(original)
# set same sample nodes for copy
new_obj.set_samples(original.sample_nodes)

# processing an event that removes facility 25, return EventReport object (works with list of Locations as well)
--
from location import Location
form event_report import EventReport
--
loc = Location(25, None, None)
report = foo.process_event(loc)
report.print_report()
```

### output 
```
link mode:
volatile
links contained in the topology
461889
facilities found within database
3474
total number of AS in topology (number of nodes in the graph)
74145
total number of locations where AS were detected
172901
lost locations:
1
lost facilities:
1
---
number of samples
20
sample nodes
[213382, 135086, 137513, 62977, 57341, 265454, 48517, 264415, 210685, 132269, 210718, 28629, 30069, 1633, 398401, 393719, 57638, 50440, 25052, 16814]
starting sampled aspl
3.71
ending sampled aspl
3.71
```

### print statistics for multiple events
```
from extended_topology import get_aggregated_results
--
fac1 = [6, 9, 11]
fac2 = [3, 22, 25, 26]
fac3 = [4, 5, 36, 326]
event1 = [Location(6,None,None), Location(9,None,None), Location(11,None,None)
event2 = ....
event3 = ....
reports = []
reports.append(foo.process_event(event1))
reports.append(foo.process_event(event2))
reports.append(foo.process_event(event3))
get_aggregated_results(reports)
--
```

### output 
```
Number of events processed:
3
maximum targets hit
4
number of events that do not hit facilities
0
average number of facility disconnected
3.6666666666666665
maximum damage sustained:
users: 108373
internet %: 0.0026
average damage:
users: 41029.666666666664
internet %: 0.001
```

# Extended Network Model Usage 

Automatically initialized when creating an ExtendedTopology object
Initialization uses same config file
Accepted values for initialization STAGE: ("START", "ASN_MAPPING", "LOCATION_MAPPING", "LINK_DETECTION", "DONE")
STAGE selects starting step for initialization: START -> ASN_MAPPING -> LOCATION_MAPPING -> LINK_DETECTION -> DONE
"START" requires no preprocessed data.
Other options require output files from all previous stages to be available
```
from extended_network_model import ExtendedNetworkModel
from utility import ExtendedConfig
---
conf = ExtendedConfig(CONFIG_FILE)
net = ExtendedNetworkModel(conf)
net.initialize(conf.STAGE, verbose=False)
```

Updates the topology by removing a list of Locations and returns Result object
```
result = net.process_impact(TARGET_LIST)
result.print()
```
### output example
```
number of removed links:2
[('39122', '196737'), ('47720', '196737')]
number of removed ASes:1
[196737]
```


Returns list of ASN in topology, reads ASN_LIST_FILE if available
```
net.get_topology_AS()
```

Print miscellaneous network and dataset measurements
```
net.print_dataset_stats()
```

### output example
```
entries in service dataset
26060
countries in service dataset
232
AS in service dataset
--
--
average node degree
12.459073437183896
top 3 AS with the largest number of neighbors (AS, degree)
[(6939, 9610), (174, 6628), (3356, 6390)]
```

Events are built from geographical coordinates and a range
```
from event_report import Event
---
ev = Event(50.5, -11.7, 300)
```

Returns list of all Locations in range of the Event
```
targets = net.get_target_locations(ev)
for t in targets:
    t.print()
```

### output 
```
{620,Cork,None}
{None,None,(51.8755, -8.493)}
{None,None,(51.8967, -8.4683)}
```


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
