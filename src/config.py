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
        self['HARM_PREFIXES']= [('/PROD/dev', 'Z:\\PROD\\dev'), 
                               ('/STUDIO', 'Z:\\STUDIO'),
                               "/opt/package/", "C:\\Program Files\\"]

        # Use built-in setup:
        self.setup()

        # If home was found, find config file:
        if self['HARM_HOME']:
            self['HARM_CONFIG'] = os.path.join(self['HARM_HOME'], "harm.config")
            # TODO:
            # Parse and apply confing file HERE:
        # or make it clear there is no config file:
        if not os.path.isfile(self['HARM_CONFIG']):
            self['HARM_CONFIG'] = None

    def setup(self):
        '''Setup default values of a class. This should be enough for Harm to operate,
        without harm.config file found.'''
        # Auto-update interval:
        self['HarmMainWindow'] = {'timer':{}}
        self['HarmMainWindow']['timer']['setInterval'] = 1000*120
        self['HarmMainWindow']['timer']['timerColor'] = (1,2,3)

        # Image viewer:
        self['image_viewer'] = '/opt/package/houdini_12.0.687/bin/mplay'

    def get_value(self, keys, _self=None, denom="/"):
        '''Providing a key in form of /key1/key2/key3 search Config 
        reqursively for a given final key. Return None on Fail.'''
        # Make sure data is correct:
        if isinstance(keys, str): 
            keys = keys.split(denom)
        else: 
            assert type(keys) in (list, tuple), \
            "Config.get_value(key) expects string, list or tuple."
        # Early exit:
        if not _self: _self = self
        if not keys[0] in _self.keys(): 
            return
        # return final value:
        if len(keys) == 1:
            return _self[keys[0]]  
        # Search deeper:
        if isinstance(_self[keys[0]], dict):
            for k, v in _self[keys[0]].iteritems():
                return self.get_value(keys[1:], _self[keys[0]])
        return None



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
        
       
           

