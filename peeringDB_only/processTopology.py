from utility import getDistance

LOCFILE = 'Dataset/201603.locations.txt'
RELFILE = 'Dataset/201603.as-rel-geo.txt'
DISTANCE = 500
CENTER_LAT = 47.112
CENTER_LON = 10.475


coordDict = {}
asLocations = {}

def checkImpact(lat, lon, size):
#find all location within 'size' from center
    targets = []
    for entry in coordDict:
        if getDistance(lat, lon, coordDict[entry][0], coordDict[entry][1]) < size:
            targets.append(entry)
    return targets

#for each AS lists the locations it operates in
with open(RELFILE) as f:
    for cnt, line in enumerate(f):
        line = line[:-1]
        vals = line.split('|')
        if int(vals[0]) not in asLocations:
            asLocations[int(vals[0])] = []
        if int(vals[1]) not in asLocations:
            asLocations[int(vals[1])] = []
        for i in vals[2:]:
            #don't need the method, only the location
            split = i.split(',')[0]
            if split not in asLocations[int(vals[0])]:
                asLocations[int(vals[0])].append(split)
            if split not in asLocations[int(vals[1])]:
                asLocations[int(vals[1])].append(split)

#collects coordinates for each  location
with open(LOCFILE) as f:
    for cnt, line in enumerate(f):
        vals = line.split('|')
        coordDict[vals[0]] = (float(vals[5]), float(vals[6]))
#print(asLinks)

targets = checkImpact(CENTER_LAT, CENTER_LON, DISTANCE)
print("LIST OF TARGETS")
print(targets)

for entry in targets:
    for location in asLocations:
        if entry in asLocations[location]:
            print("AS #")
            print(location)
            print("containing")
            print(asLocations[location])
            print("checks for")
            print(entry)
            #    for location in asLocations:
#        if entry in asLocations[location]:
            #remove entry
#            asLocations[location].pop(entry)
#            #check if no more entries are there and in case signal the AS as dead
#            if list.isEmpty(asLocations[location]):
#                print(location + "dead")


#topology



#DEBUG ONLY
#target = asLinks

#wrFilename = 'prova.txt'
#with open(wrFilename, 'w') as wrF:
#    for entry in target:
#        wrF.write(str(entry) + '|' + str(target[entry]) + " \n")
#wrF.close()


