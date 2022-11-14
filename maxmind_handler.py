from location import Location, compare_locations, check_location
import csv

NET_ASN_FILE = "./Dataset/GeoLite2-ASN-Blocks-IPv4.csv"
NET_TO_LOC = "./Dataset/GeoLite2-City-Blocks-IPv4.csv"

#returns ASN to Network mapping
def get_as_to_net(file, v=False):
    #NETWORK, ASN, AS_ORG
    as_to_net = {}
    with open(file, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            net = row[0]
            asn = int(row[1])
            if asn not in as_to_net.keys():
                as_to_net[asn] = []
            as_to_net[asn].append(str(net))
        f.close()
    return as_to_net

#returns net : {Location}
#network, geo_id, country_geo_id, represented_country_geo_id, is anonymous, is satellite, postal code, latitude, longitude, accuracy
def get_net_to_location(file):
    net_to_loc = {}
    with open(file, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            net = str(row[0])
            lat = row[7]
            lon = row[8]
            if lat != '' and lon != '':
                loc = Location()
                loc.coord = (float(lat), float(lon))
                if net not in net_to_loc.keys():
                    net_to_loc[net] = []
                if not check_location(loc, net_to_loc[net]):
                    net_to_loc[net].append(loc)
        f.close()
    return net_to_loc

#returns ASN : {Location list}
def get_geolite_locations(v=False):
    #reading CSV file for dictionaries
    as_to_net = get_as_to_net(NET_ASN_FILE)
    if v:
        print("ASN in as_to_net")
        print(len(as_to_net))
    net_to_loc = get_net_to_location(NET_TO_LOC)
    if v:
        print("networks in net_to_loc")
        print(len(net_to_loc))

    #joining dictionaries
    if v:
        print("joining dictionaries")
    as_to_loc = {}


    for asn in as_to_net:
        if len(as_to_net[asn]) != 0:
            for net in as_to_net[asn]:
                if net in net_to_loc.keys():
                    for loc in net_to_loc[net]:
                        if asn not in as_to_loc.keys():
                            as_to_loc[asn] = []
                        if not check_location(loc, as_to_loc[asn]):
                            as_to_loc[asn].append(loc)

    return as_to_loc