#IXPDB DATASET EXTRACTOR AND AS TO FACILITY MAPPING

import pandas as pd
import csv
import json
from location import Location, check_location, compare_locations

ASN_FILE = ".\Dataset\\asn-dataset.csv"
IXP_FILE = ".\Dataset\\ixp-dataset.csv"
IXP_SWITCH_FILE = ".\Dataset\\asn-by-ixp-switch.csv"

def get_asn_dataset(file):
    # ASN,CC,Name,IXP Number (IX-F ID),Switch Name,IPv4 Address,IPv6 Address,MAC Address,Vendor,MANRS,IXP Switch
    # ixp: {asn list}
    ixp_dict = {}
    with open(file, 'r', encoding='UTF8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row[3] not in ixp_dict.keys():
                ixp_dict[row[3]] = []
            elif row[0] not in ixp_dict[row[3]]:
                ixp_dict[row[3]].append(int(row[0]))
        f.close()

    return ixp_dict

#returns ixp: {location list}
def get_ixp_dataset(file):
    # IXP Number (IX-F ID),Name,Metro,Switch Name,Switch Model,Software Version,Peering DB Facility ID,
        # Coordinates,IPv4,IPv6,MANRS,ASN Sum,IXP Switch
    location_dict = {}
    with open(file, 'r', encoding='UTF8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row[2] == "" and row[6] == "" and row[7] == "":
                continue
            loc = Location()
            if row[0] not in location_dict.keys():
                location_dict[row[0]] = []
            if row[2] != "":
                loc.city = row[2]
            if row[6] != "":
                loc.facility = int(row[6])
            if row[7] != "":
                s = row[7].split(',')
                loc.coord = (float(s[0]), float(s[1]))
            if not check_location(loc, location_dict[row[0]]):
                location_dict[row[0]].append(loc)
        f.close()
        return location_dict

def get_as_to_ixp_dataset(file):
    #(as, ixp) : location list
    as_ixp_dict = {}
    with open(file, 'r', encoding='UTF8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            index = (int(row[0]), row[3])
            loc = Location()
            if index not in as_ixp_dict.keys():
                as_ixp_dict[index] = []
            if row[11] == "" and row[14] == "" and row[15] == "":
                continue
            if row[11] != "":
                loc.city = row[11]
            if row[14] != "":
                loc.facility = int(row[14])
            if row[15] != "":
                s = row[15].split(',')
                loc.coord = (float(s[0]), float(s[1]))
            if not check_location(loc, as_ixp_dict[index]):
                as_ixp_dict[index].append(loc)
        f.close()
        return as_ixp_dict


# as: {location list}
def unite_dict(ixp_as, ixp_loc, as_ixp_loc):
    as_loc_dict = {}
    # look for all ixp in ixp_as
    for i1 in ixp_as:
        #look for location associated with i1
        if i1 in ixp_loc.keys():
            #assign to all ASN of i1 the location
            if len(ixp_as[i1]) != 0:
                for a1 in ixp_as[i1]:
                    if a1 not in as_loc_dict.keys():
                        as_loc_dict[a1] = []
                    if len(ixp_loc[i1]) != 0:
                        for loc in ixp_loc[i1]:
                            if not check_location(loc, as_loc_dict[a1]):
                                as_loc_dict[a1].append(loc)
    #look for all as in as_ixp_loc
    for key in as_ixp_loc:
        a2 = key[0]
        if len(as_ixp_loc[key]) != 0:
            if a2 not in as_loc_dict.keys():
                as_loc_dict[a2] = []
            for loc in as_ixp_loc[key]:
                if not check_location(loc, as_loc_dict[a2]):
                    as_loc_dict[a2].append(loc)
    return as_loc_dict

def get_additional_locations(f1 = ASN_FILE, f2 = IXP_FILE, f3 = IXP_SWITCH_FILE):
    #build a dictionary with all possible AS to be found
    ixp_as_dict = get_asn_dataset(f1)
    ixp_location_dict = get_ixp_dataset(f2)
    as_ixp_loc_dict = get_as_to_ixp_dataset(f3)
    as_loc_dict = unite_dict(ixp_as_dict, ixp_location_dict, as_ixp_loc_dict)


    return as_loc_dict