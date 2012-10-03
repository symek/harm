import sys
try: 
    import json
except: 
    try:
        import simplejson as json
    except:
        raise ImportError("No json nor simplejson found.")

class Config(dict):
    def __init__(self, _dict={}):
        super(self.__class__, self).__init__(_dict)
    def load(self, filename):
        file = open(filename, 'r')
        _dict = json.load(file)
        super(self.__class__, self).__init__(_dict)
    def dump(self, filename, indent=4):
        file = open(filename, 'w')
        json.dump(self, file, indent=indent)
        file.close()
