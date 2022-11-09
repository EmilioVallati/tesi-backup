#OPEN-RISOP DATASET EXTRACTION
SCENARIO = "./Dataset/countervalue.csv"
import pandas as pd
import csv
from extended_topology import Event

#Only these values are present in the RISOP dataset.
#function to get radius from arbitrary yield, height of burst must be implemented
def get_radius(yld, hob):
    #return value expressed in km
    if yld == 100:
        if hob == 840:
            return 5.15
        else:
            return 3.62
    elif yld == 200:
        if hob == 1060:
            return 6.49
        else:
            return 4.56
    elif yld == 250:
        if hob == 1150:
            return 6.99
        else:
            return 4.91
    elif yld == 800:
        if hob == 1690:
            return 10.3
        else:
            return 7.24

def get_scenario(file=SCENARIO, verbose=False):
    #LATITUDE, LONGITUDE, NAME, DESCRIPTION, YIELD, HOB
    eventList = []
    if verbose:
        print("Reading events from " + str(file) + '\n')

    with open(file, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            latitude = float(row[0])
            longitude = float(row[1])
            radius = get_radius(int(row[4]), int(row[5]))
            e = Event(latitude, longitude, radius)
            eventList.append(e)
        f.close()
    return eventList

