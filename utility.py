from haversine import haversine, Unit
import configparser
import os.path
from geopy import Nominatim

class ExtendedConfig:
    def __init__(self, conf_file = None):
        config = configparser.ConfigParser()
        config.read(conf_file)
        if "extended" not in config:
            print("invalid conf file!")
            raise Exception
        else:
            #ixpdb dataset files
            if 'IXPDB_ASN_FILE' in config['extended'] and 'IXPDB_IXP_FILE' in config['extended'] \
                    and 'IXPDB_ASN_IXP_FILE' in config['extended']:
                self.IXPDB_ASN_FILE = config['extended']['IXPDB_ASN_FILE']
                self.IXPDB_IXP_FILE = config['extended']['IXPDB_IXP_FILE']
                self.IXPDB_ASN_IXP_FILE = config['extended']['IXPDB_ASN_IXP_FILE']
            else:
                print("undefined ixpdb dataset files")
                raise Exception

            #preprocessed data files
            if 'CITY_COORD_FACILITIES' in config['extended']:
                self.CITY_COORD_FACILITIES = config['extended']['CITY_COORD_FACILITIES']
            else:
                print("undefined file for city coordinates for facilities")
                raise Exception

            if 'CITY_COORD_ASN' in config['extended']:
                self.CITY_COORD_ASN = config['extended']['CITY_COORD_ASN']
            else:
                print("undefined file for city coordinates for ASN")
                raise Exception

            if 'FACILITY_COORD_FILE' in config['extended']:
                self.FACILITY_COORD_FILE = config['extended']['FACILITY_COORD_FILE']
            else:
                print("undefined facility to coordinate mapping file")
                raise Exception

            if 'FACILITY_ASN_FILE' in config['extended']:
                self.FACILITY_ASN_FILE = config['extended']['FACILITY_ASN_FILE']
            else:
                print("undefined facility to ASN mapping file")
                raise Exception

            if 'ASN_LOCATION_FILE' in config['extended']:
                self.ASN_LOCATION_FILE = config['extended']['ASN_LOCATION_FILE']
            else:
                print("undefined ASN location mapping file")
                raise Exception

            if 'ASN_LIST_FILE' in config['extended']:
                self.ASN_LIST_FILE = config['extended']['ASN_LIST_FILE']
            else:
                print("undefined list of topology ASN file")
                raise Exception

            # population data for AS network
            if 'CUSTOMER_FILE' in config['extended']:
                self.CUSTOMER_FILE = config['extended']['CUSTOMER_FILE']
            else:
                print("undefined customer file")
                raise Exception

            # topology dataset
            if 'RELFILE' in config['extended']:
                self.RELFILE = config['extended']['RELFILE']
            else:
                print("undefined topology file")
                raise Exception

            # cached topology for quick init
            if 'LINKFILE' in config['extended']:
                self.LINKFILE = config['extended']['LINKFILE']
            else:
                print("undefined topology cache file")
                raise Exception

            # peeringdb facility db
            if 'DBFILE' in config['extended']:
                self.DBFILE = config['extended']['DBFILE']
            else:
                print("undefined database file")
                raise Exception

            # log file
            if 'LOGFILE' in config['extended']:
                self.LOGFILE = config['extended']['LOGFILE']
            else:
                print("undefined log file")
                raise Exception

            # number of samples for average measurements
            if 'NUMSAMPLES' in config['extended']:
                m = config['extended']['NUMSAMPLES']
                if int(m) > 0:
                    self.NUMSAMPLES = m
                else:
                    raise Exception
            else:
                print("undefined sample number")
                raise Exception

            #conservative or volatile nodes mode
            if 'MODE' in config['extended']:
                m = config['extended']['MODE']
                if m == 'volatile':
                    self.MODE = m
                elif m == 'stable':
                    print("stable mode not supported for the extended version of the dataset")
                    raise Exception
                else:
                    print("Only 'volatile' or 'stable' values allowed for MODE")
                    raise Exception
            else:
                print("undefined mode")
                raise Exception

            #full init or load previous topology
            if 'STAGE' in config['extended']:
                m = config['extended']['STAGE']
                if m == 'START' or m == 'ASN_MAPPING' or m == 'LOCATION_MAPPING' or m == 'LINK_DETECTION' or m == 'DONE':
                    self.STAGE = m
                else:
                    print("Only 'START', 'ASN_MAPPING', 'LOCATION_MAPPING', 'LINK_DETECTION', 'DONE' allowed")
                    raise Exception
            else:
                print("undefined stage ")
                raise Exception

def copy_location_dict(dict):
    ret = {}
    for k in dict.keys():
        ret[k] = []
        for l in dict[k]:
            ret[k].append(l)
    return ret

def get_distance(lat1, lon1, lat2, lon2):
    src = (lat1, lon1)
    dest = (lat2, lon2)
    ret = haversine(src, dest)
    return ret

#returns detectableLinks dictionary
def read_rebuilt_links(file):
    links = {}
    # preparing topology
    with open(file) as f:
        for cnt, line in enumerate(f):
            line = line[:-1]
            vals = line.split('|')
            link = str(vals[0])
            link = link[1:-1]
            del vals[0]
            # print(vals)
            k = link.split(", ")
            key = (k[0], k[1])
            links[key] = []
            for v in vals:
                links[key].append(int(v))
        f.close()
    return links

#returns list of links
def read_full_links(file, verbose=False):
    links_list = []
    if verbose:
        print("reading links from "+ str(file))
    with open(file) as f:
        for cnt, line in enumerate(f):
            if line[0] != '#':
                vals = line.split('|')
                link = (int(vals[0]), int(vals[1]))
                links_list.append(link)
    f.close()
    return links_list


#returns a dictionary with coordinates assigned to a list of city names
def get_city_coord(city_list, file, v=False):
    #if file exists, we read, otherwise we send request to locator, then write the file
    city_to_coord = {}
    if os.path.exists(file):
        if v:
            print("reading city coordinates from file")
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                l = line.split(':')
                city = l[0]
                lat = float(l[1].split(',')[0][1:])
                lon = float(l[1].split(',')[1][:-2])
                city_to_coord[city] = (lat, lon)

    else:
        if v:
            print("requesting city coordinates from geocoder")
        locator = Nominatim(user_agent="myGeocoder")
        for c in city_list:
            location = locator.geocode(c)
            if location is not None:
                lat = float(location.latitude)
                lon = float(location.longitude)
                city_to_coord[c] = (lat, lon)
                if v:
                    print(str(c) + " (" + str(lat) + "," + str(lon) +")")
        if v:
            print("saving coordinates to " + str(file))
        with open(file, 'w', encoding='utf-8') as f:
            for k in city_to_coord:
                f.write(k)
                f.write(':(')
                f.write(str(city_to_coord[k][0]))
                f.write(',')
                f.write(str(city_to_coord[k][1]))
                f.write(')\n')
            f.close()
    return city_to_coord
