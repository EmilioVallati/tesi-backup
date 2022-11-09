######## OLD CONFIG FILE ########
class Config:
    def __init__(self, conf_file = None):
        config = configparser.ConfigParser()
        config.read(conf_file)
        if 'nuclear_warfare' not in config:
            print("invalid conf file!")
            raise Exception
        else:
            # population data for AS network
            if 'CUSTOMER_FILE' in config['nuclear_warfare']:
                self.CUSTOMER_FILE = config['nuclear_warfare']['CUSTOMER_FILE']
            else:
                print("undefined customer file")
                raise Exception

            # topology dataset
            if 'RELFILE' in config['nuclear_warfare']:
                self.RELFILE = config['nuclear_warfare']['RELFILE']
            else:
                print("undefined topology file")
                raise Exception

            # cached topology for quick init
            if 'LINKFILE' in config['nuclear_warfare']:
                self.LINKFILE = config['nuclear_warfare']['LINKFILE']
            else:
                print("undefined topology cache file")
                raise Exception

            # peeringdb facility db
            if 'DBFILE' in config['nuclear_warfare']:
                self.DBFILE = config['nuclear_warfare']['DBFILE']
            else:
                print("undefined database file")
                raise Exception

            # log file
            if 'LOGFILE' in config['nuclear_warfare']:
                self.LOGFILE = config['nuclear_warfare']['LOGFILE']
            else:
                print("undefined log file")
                raise Exception

            # number of samples for average measurements
            if 'NUMSAMPLES' in config['nuclear_warfare']:
                m = config['nuclear_warfare']['NUMSAMPLES']
                if int(m) > 0:
                    self.NUMSAMPLES = m
                else:
                    raise Exception
            else:
                print("undefined sample number")
                raise Exception

            # number of events between measurements
            if 'NUMEVENTS' in config['nuclear_warfare']:
                m = config['nuclear_warfare']['NUMEVENTS']
                if int(m) > 0:
                    self.NUMEVENTS = m
                else:
                    raise Exception
            else:
                print("undefined sample frequency")
                raise Exception
            #conservative or volatile nodes mode
            if 'MODE' in config['nuclear_warfare']:
                m = config['nuclear_warfare']['MODE']
                if m == 'volatile':
                    self.MODE = m
                elif m == 'stable':
                    print("stable mode unsupported for the extended version")
                    raise Exception
                else:
                    print("Only 'volatile' or 'stable' values allowed for MODE")
                    raise Exception
            else:
                print("undefined mode")
                raise Exception
            #full init or load previous topology
            if 'FULL_INIT' in config['nuclear_warfare']:
                m = config['nuclear_warfare']['FULL_INIT']
                if m == 'True' or m == 'False':
                    self.FULL_INIT = m
                else:
                    print("Only 'True' or 'False' values allowed for FULL_INIT")
                    raise Exception
            else:
                print("undefined mode")
                raise Exception
