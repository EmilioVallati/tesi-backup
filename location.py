#When using Locations, types of data with higher reliability have priority
#Facility refers to peeringDB's facility ID

class Location():
    def __init__(self, facility=None, city=None, coord=None):
        #int
        self.facility = facility
        #string
        self.city = city
        #(float, float)
        self.coord = coord
    def print(self):
        print('{' + str(self.facility) + ',' + str(self.city) + ',' + str(self.coord) + '}')

#two locations are equivalent if their highest priority value is the same
#priority checks for facility, then city, then coord to reduce number of different entries providing same information
def compare_locations(loc1, loc2):
    if loc1.facility is not None and loc2.facility is not None:
        return loc1.facility == loc2.facility
    elif loc1.city is not None and loc2.city is not None:
        return loc1.city == loc2.city
    elif loc1.coord is not None and loc2.coord is not None:
        if loc1.coord[0] == loc2.coord[0] and loc1.coord[1] == loc2.coord[1]:
            return True
    else:
        return False

#Checks if there is an equivalent location for loc inside loc_list
def check_location(loc, loc_list):
    if not isinstance(loc, Location):
        print("loc")
        print(loc)
        print("not a location")
    for ll in loc_list:
        if not isinstance(ll, Location):
            print("l")
            print(ll)
            print("not a location")
            return False
        if compare_locations(loc, ll) is True:
            return True
    return False
