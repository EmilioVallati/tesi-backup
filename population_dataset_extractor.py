import re
HTML_FILE = "Dataset/customers-per-as-measurements.html"

# small html parser for customer serviced by ASNs
def parse_service(file):
    lines = []
    serviceDict = {}
    with open(file) as f:
        for cnt, l in enumerate(f):
            result = re.findall('\[(.*)\]', l)
            for i in result:
                if '0' <= i[0] <= '9':
                    lines.append(i)
        f.close()
    for s in lines:
        vals = s.split(',')
        #index key
        serviceDict[vals[0]] = []
        #ASN
        asn = vals[1][3:-1]
        serviceDict[vals[0]].append(int(asn))
        #Country Code
        cc = vals[-5][-7:-5]
        serviceDict[vals[0]].append(str(cc))
        #Users
        serviceDict[vals[0]].append(int(vals[-4]))
        #country %
        serviceDict[vals[0]].append(float(vals[-3]))
        #internet %
        serviceDict[vals[0]].append(float(vals[-2]))
    return serviceDict

