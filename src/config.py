import sys, os
try: 
    import json
except: 
    try:
        import simplejson as json
    except:
        raise ImportError("No json nor simplejson found.")


# Python 2.6 compatibility:
try:
    from collections import OrderedDict, defaultdict
except ImportError:
    from ordereddict import OrderedDict

import utilities


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

        self['image_viewer'] = [('mplay', ""), ('rv', ""),  ("iv", ""), ("djv_view", ""), ('fcheck', "")]
        self['file_manager'] = [('nautilus', "")]




        # self.selectedC.setHsvF(0.108, 0.95, 1)
        # self.waitingC.setHsvF(0.30, 0.3, 1)
        # self.progresC.setHsvF(0.0, 0.2, 1)
        # self.finisheC.setHsvF(0.69, 0.2, 1)
        # self.hqwC = QColor()
        # self.hqwC.setHsvF(.15, .2, 1)
        # self.qwC = QColor()
        # self.qwC.setHsvF(.30, .2, 1)
        # self.qwWaitingC = QColor()
        # self.qwWaitingC.setHsvF(.6, .2, 1)

    def set_value(self, keys, value, _self=None, denom='/'):
        # Make sure data is correct:
        # FIXME: broken.
        if isinstance(keys, str): 
            keys = keys.split(denom)
        else: 
            assert type(keys) in (list, tuple), \
            "Config.set_value(key) expects string, list or tuple."
        if not _self: _self = self
        if len(keys) == 1:
            _self[keys[0]] = value
            print "I set %s in %s" % (value, str(_self[keys[0]]))
            return True
        if keys[0] in _self.keys():
            if isinstance(_self(keys[0]), dict):
                return self.set_value(keys[1:], value, _self(keys[0]))
        else:
            _self[keys[0]] = {}
            return self.set_value(keys[1:], value, _self[keys[0]])
        return False
       


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
        '''Converts  paths between different platforms (OS).'''
        # FIXME: How aboud Darwin?
        linux = 0; windows = 1; 
        if sys.platform in ('win32', 'win64'):
            for prefix in self['HARM_PREFIXES']:
                if path.startswith(prefix[linux]):
                    path = path.replace(prefix[linux], prefix[windows])
                    path = os.path.normpath(path)
                    break      
        elif sys.platform in ('linux2'):
            for prefix in self['HARM_PREFIXES']:
                if path.startswith(prefix[windows]):
                    path = path.replace(prefix[windows], prefix[linux])
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

    def select_optional_executable(self, field):
        """ We try to choose amount avaible tools specified
            optianally in a class like image_viewer or file_manager.
        """
        # self.config['image_viewer'] is a list of a number of viewers
        # [('rv', ""), ...], second tuple element is optional path.
        # If None, it is to be found in PATH,
        
        for candidate in self[field]:
            assert(len(candidate) == 2)
            exec_, path = candidate
            if not path:
                exec_ = utilities.which(exec_)
                if exec_:
                    return exec_
            else:
                path = self.convert_platform_path(path)
                if os.path.isfile(path):
                    return path
        return None

        
       
           

