import sys, os
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
        # Overwrite with environmental variables:
        self['HARM_HOME']  = os.getenv("HARM_HOME", None)
        # If not guess from self location:
        if not self['HARM_HOME']:
            self['HARM_HOME'] = os.path.join(os.path.split(__file__)[0], "../")
            self['HARM_HOME'] = os.path.normpath(self['HARM_HOME'])

        # Standard sub-paths:
        self['HARM_ICON']   = os.getenv("HARM_ICON",   os.path.join(self['HARM_HOME'], "icons"))
        self['HARM_SCRIPT'] = os.getenv("HARM_SCRIPT", os.path.join(self['HARM_HOME'], "scripts"))
        self['HARM_MENU']   = os.getenv("HARM_MENU",   os.path.join(self['HARM_HOME'], "menu"))
        self['HARM_PREFIXES']= [('/PROD/dev', 'Z:/PROD/dev'), 
                               ('/STUDIO', 'Z:/STUDIO')]

        # Auto-update interval:
        self['HarmMainWindow'] = {'timer':{}}
        self['HarmMainWindow']['timer']['setInterval'] = 1000*120

        # If home was found, find config file:
        if self['HARM_HOME']:
            self['HARM_CONFIG'] = os.path.join(self['HARM_HOME'], "../config.xml")
            # TODO:
            # Parse and apply confing file HERE:
        # or make it clear there is no config file:
        if not os.path.isfile(self['HARM_CONFIG']):
            self['HARM_CONFIG'] = None

    def load(self, filename):
        '''Loads and apply an entire config file.'''
        file = open(filename, 'r')
        _dict = json.load(file)
        super(self.__class__, self).__init__(_dict)

    def dump(self, filename, indent=4):
        '''Dump to file whole class.'''
        file = open(filename, 'w')
        json.dump(self, file, indent=indent)
        file.close()

    def convert_platform_path(self, path):
        '''Converts linux paths into Windows one and vice versa.'''
        # FIXME: How aboud Darwin?
        if sys.platform in ('win32', 'win64'):
            for prefix in self['HARM_PREFIXES']:
                if path.startswith(prefix[0]):
                    path = path.replace(prefix[0], prefix[1])
                    path = os.path.normpath(path)
                    print path
                    break
                    
        elif sys.platform in ('linux2'):
            for prefix in self['HARM_PREFIXES']:
                if path.startswith(prefix[1]):
                    path = path.replace(prefix[1], prefix[0])
                    path = os.path.normpath(path)
                    break
        return path

    def get_harm_path(self, file, subpath='HARM_HOME'):
        '''Return joined path for a provided file.'''
        # TODO: This should find an actual file in folders mentioned
        # in locations, that is HARM_ICON should be a list of paths, not
        # a single path.
        path = os.path.join(self[subpath], file)
        return self.convert_platform_path(path)

    def get_icon_path(self, file):
        '''Shorcut to return icons path for a provided name.'''
        return self.get_harm_path(file, 'HARM_ICON')
        
       
           

