from PyQt4.QtCore import *
import tokens
import utilities
import views
import os
from ordereddict import OrderedDict
import couchdb as cdb

##########################################################
# Xml****Config are work-horses in custom Qt models      #
##########################################################

## {{{ http://code.activestate.com/recipes/410469/ (r5)
from xml.etree import ElementTree

class XmlListConfig(list):
    def __init__(self, aList):
        for element in aList:
            if element:
                # treat like dict
                if len(element) == 1 or element[0].tag != element[1].tag:
                    self.append(XmlDictConfig(element))
                # treat like list
                elif element[0].tag == element[1].tag:
                    self.append(XmlListConfig(element))
            elif element.text:
                text = element.text.strip()
                if text:
                    self.append(text)


class XmlDictConfig(dict):
    '''
    Example usage:

    >>> tree = ElementTree.parse('your_file.xml')
    >>> root = tree.getroot()
    >>> xmldict = XmlDictConfig(root)

    Or, if you want to use an XML string:

    >>> root = ElementTree.XML(xml_string)
    >>> xmldict = XmlDictConfig(root)

    And then use xmldict for what it is... a dict.
    '''
    def __init__(self, parent_element):
        if parent_element.items():
            self.update(dict(parent_element.items()))
        for element in parent_element:
            if element:
                # treat like dict - we assume that if the first two tags
                # in a series are different, then they are all different.
                if len(element) == 1 or element[0].tag != element[1].tag:
                    aDict = XmlDictConfig(element)
                # treat like list - we assume that if the first two tags
                # in a series are the same, then the rest are the same.
                else:
                    # here, we put the list in dictionary; the key is the
                    # tag name the list elements all share in common, and
                    # the value is the list itself 
                    aDict = {element[0].tag: XmlListConfig(element)}
                # if the tag has attributes, add those to the dict
                if element.items():
                    aDict.update(dict(element.items()))
                self.update({element.tag: aDict})
            # this assumes that if you've got an attribute in a tag,
            # you won't be having any text. This may or may not be a 
            # good idea -- time will tell. It works for the way we are
            # currently doing XML configuration files...
            elif element.items():
                self.update({element.tag: dict(element.items())})
                
            # finally, if there are no child tags and no attributes, extract
            # the text
            else:
                self.update({element.tag: element.text})
## end of http://code.activestate.com/recipes/410469/ }}}


# #####################################################
#  Input text is an output from qccet SGE utility     #
########################################################

def qccet_to_dict(text, tasks=False, order_list=None):
    def getValue(value):
        if value.isdigit(): 
            value = int(value)
        else:
            try: 
                value = float(value)
            except: 
                pass
        return value
    def reorder_dict(d, l):
        out = OrderedDict()
        left = []
        for key in l:
            if key in d.keys():
                out[key] = d[key]
        for key in d:
            if key not in out:
                out[key] = d[key]
        return out

    f = text.split(62*"=")
    out = OrderedDict()
    for job in f:
        j = OrderedDict()
        job = job.split("\n")
        for tag in job:
            tag = tag.strip().split()
            if len(tag) > 1:
                j[tag[0]] = getValue(" ".join(tag[1:]))
        if order_list: 
            j = reorder_dict(j, order_list)
        if j.keys():
            if not tasks:
                out[str(j['jobnumber'])] = j
            else:
                out[".".join([str(j['jobnumber']), str(j['taskid'])])] = j
    return out


def rotate_nested_dict(d, key):
    '''Given a dictionary of dictionarties, it builds a new one
       with keys taken from children's values.'''
    output = OrderedDict()#{}
    for item in d:
        if key in d[item]:
            if d[item][key] not in output.keys():
                output[d[item][key]] = [d[item]]
            else:
                output[d[item][key]].append(d[item])
    return output


#################################################################
#               Sge Abstract (base) Model                       #   
# ###############################################################

class SgeTableModelBase():
    def __init__(self, parent=None):
        self.sge_view = parent
        print "Initializing SgeTableModelBase."
        '''_tree is an ElementTree as parsed stright from a XML.
           _xml is stripped version of a tree in dict() format.
           _data is list of the lists version of item in _xml.
           _head is a dict of headers found in xml items.'''
        self._tree = None
        self._dict = OrderedDict()
        self._data = []
        self._head = OrderedDict()

    def flags(self, index):
        flag = super(self.__class__, self).flags(index)
        return flag | Qt.ItemIsEditable

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        if len(self._data):
            return len(self._data[-1])
        return 0

    def _tag2idx(self, item):
        '''This builds self._head dict {1:header, 2:another, ...}'''
        _map = OrderedDict()
        for x in range(len(item.keys())):
            _map[x] = item.keys()[x]
        return _map

    def data_hooks(self, index, value):
        '''Loops through all hook_* function of self, and executes it
           to preprocess data of a model. Hooks to be provided by derived classes'''
        for func in dir(self):
            if func.startswith("hook"):
                value = self.__getattribute__(func)(index, value)

        # Process data types: 
        if value == None: 
            return None
        elif value.__class__ in (int, float):
            return value 
        elif not isinstance(value, str):
            return None
        if value.isdigit(): 
            value = int(value)
        try: 
            value = float(value)
        except: 
            pass
        return value

    def get_key_index(self, key):
        '''Returns a key index in headers given its name.'''
        if key in self._head.values():
            return [k for k, v in self._head.iteritems() if v == key][0]
              
    def data(self, index, role):
        ''''Data access.'''
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()

        # Read element from a elementTree sub-entry :
        value  = None
        try:
            value = self._data[index.row()][index.column()]
            value = self.data_hooks(index, value)
        except:
            print self
        if not value: return QVariant()        
        # Finally return something meaningfull:
        return QVariant(value)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        '''Headers builder. Note crude tokens replacement.'''
        # Replaces columns/rows names view custom tokens;
        def header_replace(name):
            if name in tokens.header.keys():
                name = tokens.header[name]
            return name
        # Nothing to do here:
        if role != Qt.DisplayRole:
            return QVariant()
        # Horizontal headers:
        if orientation == Qt.Horizontal and len(self._data):
            if section in self._head:
                return QVariant(header_replace(self._head[section]))
            return QVariant()
        # Vertical headers:
        elif orientation == Qt.Vertical and len(self._data):
                return QVariant(header_replace(int(section+1)))
        return QVariant()

    def parse_time_string(self, time):
        '''Parses the time string to reasonable format.'''
        date, time = time.split("T")
        return " ".join((time, date))

    def get_value(self, key, data=None):
        '''Searches data model for particular value based on provided key. 
        Returns a list of values (multiply occurance of key are possible),
        or empty list. It should handle multi-nested dictionaries and lists. 
        Note: it is very expensive. perhaps we should cache it.'''
        def find(key, value):
            '''http://stackoverflow.com/questions/9807634/\
            find-all-occurences-of-a-key-in-nested-python-dictionaries-and-lists'''
            for k, v in value.iteritems():
                if k == key:
                    yield v
                elif isinstance(v, dict):
                    for result in find(key, v):
                        yield result
                elif isinstance(v, list):
                    for d in v:
                        if isinstance(d, dict):
                            for result in find(key, d):
                                yield result
                        for result in find(key, d):
                            yield result
        # Data is our own:
        if not data:
            data = self._dict
        # Return non-empy list:
        result = list(find(key, data))
        if len(result) > 0:
            return result
        else:
            # Overwise search for 'hidden' variables:
            names = list(find("VA_variable", data))
            value = list(find("VA_value", data))
            if key in names:
                index = names.index(key)
                return [value[index]]
        return []

    ####################################################################
    # hook_*'s are pickedup automatically by SgeTableModelBase.data()  #
    # when building table's items.                                     #
    # ##################################################################
    def hook_timestring(self, index, value):
        # Change time string formating:
        if self._head[index.column()] in tokens.time_strings: 
            # Parse time string diffrently for tasks view:
            if self._head[index.column()] == "JAT_start_time":
                value = utilities.string_to_elapsed_time(value)
            else: 
                value = self.parse_time_string(value)
        return value

    def hook_machinename(self, index, value):
        # Shorten machine name in Tasks view:
        if self._head[index.column()] == 'queue_name':
            if value: 
                value = value.split("@")[-1]
                if "." in value:
                    value = value.split(".")[0]
        return value



#################################################################
#               Database Table Model Base                       #
# This class enable minimal  databse support for sge models     #
# Current couchdb should be replaced by some abstraction layer! #
# ###############################################################


class CdbTableModel():
    '''Query jobs information from couchdb database. There is a single method
    append_jobs_history which queries db using standard python couchdb module.
    This class is meant to be inherited by other models like JobsModel.'''
    def append_jobs_history(self):
        '''Append history from couchdb database'''
        def convert_to_sge_time(t, sge_time_format = "%Y-%m-%dT%H:%M:%S"):
            '''Epoc to sge time string convertion.'''
            import time, datetime
            return  time.strftime(sge_time_format, time.gmtime(float(t)))
        # A list of a jobs currently rendered or queued
        # (thus whose kept track by SGE):
        current_jobs = self._dict.keys()
        # We need this!
        try:
            server = cdb.Server(os.getenv("CDB_SERVER"))    
            db     = server['sge_db']
        except:
            return
        # This is our map function with hand crafted requests fields:
        # It mimics qstat data, with a state replaced by 'cdb', which will allow us 
        # to treat it differently down the stream.
        map_   = ''' function(doc) {
            var js  = doc.JB_ja_structure.task_id_range;
            var jss = "".concat(js.RN_min, "-", js.RN_max, ":", js.RN_step);
            var que = doc.JB_hard_queue_list.destin_ident_list.QR_name;
            emit(doc._id, [doc.JB_owner, "cdb", jss, doc.JB_priority, doc. JB_job_name, "1", \
                 que, doc.JB_job_number, doc.JB_submission_time])
        }'''
        query = db.query(map_).rows
        query = [x.value for x in query]
        query.reverse()
        # Convert a time string and remove jobs which were
        # returned by qstat:
        for item in range(len(query)):
            if query[item][-2] not in current_jobs:
                # FIXME: Instead of converting it to sge-ugly-string, we
                # should convert qstat query to epoc float, and convert it
                # in delegates!
                query[item][-1] = convert_to_sge_time(query[item][-1])
            else:
                query.remove(item)
        # Merge cdb with qstat:
        self._data += query

    def update_job_details_db(self, job_id, map_f="function(doc) { emit(doc._id, doc) }", 
                              sort_by_field="",  reverse_order=False):
        '''Retrieves job details from database.'''
        from structured import dict2et
        server = cdb.Server(os.getenv("CDB_SERVER"))
        db     = server['sge_db']
        job    = db.query(map_f, key=job_id).rows 
        if len(job) > 0:
            job = job[0].value
            cdb_dict = OrderedDict(job)
            return cdb_dict
        return OrderedDict()




#################################################################
#               Machine Table Model Base                        #
# The only difference is headerData which takes machine name as #
# the row name.                                                 #
# ###############################################################
class MachineModelBase(SgeTableModelBase):
    def __init__(self, parnet=None):
        super(self.__class__, self).__init__(parent)


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        '''Headers builder. Note crude tokens replacement.'''
        # Replaces columns/rows names view custom tokens;
        def header_replace(name):
            if name in tokens.header.keys():
                name = tokens.header[name]
            return name
        # Nothing to do here:
        if role != Qt.DisplayRole:
            return QVariant()
        # Horizontal headers:
        if orientation == Qt.Horizontal and len(self._data):
            return QVariant(header_replace(self._head[section]))
        # Vertical headers:
        elif orientation == Qt.Vertical and len(self._data):
            return QVariant(header_replace(self._dict.keys()[section]))
        return QVariant()



#################################################################
#               Job Table Model                                 #   
# ###############################################################

class JobsModel(QAbstractTableModel, SgeTableModelBase, CdbTableModel):
    def __init__(self,  parent=None, *args):
        super(self.__class__, self).__init__(parent)
        self.sge_view = parent
        self._tree = None
        self._data = []
        self._head = OrderedDict()

    def update(self, sge_command, token='job_info', sort_by_field='JB_job_number', reverse_order=True):
        '''Main function of derived model. Builds _data list from input.'''
        from operator import itemgetter
        # All dirty data. We need to duplicate it here,
        # to keep things clean down the stream.
        self._tree = ElementTree.parse(os.popen(sge_command))
        self._dict  = XmlDictConfig(self._tree.getroot())[token]
        self._data = []
        self._head = OrderedDict()

        # XmlDictConfig returns string instead of dict in case *_info are empty! Grrr...!
        if isinstance(self._dict, dict):
            d = self._dict['job_list']
            if isinstance(d, list):
                self._head = self._tag2idx(d[-1])
                self._data += [[x[key] for key in x.keys()] for x in d]
            elif isinstance(d, dict):
                self._head = self._tag2idx(d)
                self._data = [d.values()]
                # Sort list by specified header (given it's name, not index):
                if sort_by_field in self._head.values() and len(self._data) > 0:
                    key_index = self.get_key_index(sort_by_field)
                    self._data = sorted(self._data,  key=itemgetter(key_index))
                    if reverse_order:
                        self._data.reverse()
            


#################################################################
#               Tasks Table Model                               #   
# ###############################################################

class TaskModel(QAbstractTableModel, SgeTableModelBase, CdbTableModel):
    ''''''
    def __init__(self,  parent=None, *args):
        super(self.__class__, self).__init__(parent)
        # JobsModel.__init__(self, parent)
        self.sge_view = parent
        self._tree = None
        self._data = []
        self._head = OrderedDict()

    def update_db(self, job_id, token=""):
        data = self.update_job_details_db(job_id)
        tasks  = self.get_value("JB_ja_tasks", data)
        if len(tasks):
            tasks = tasks[0]['ulong_sublist']
            print job_id + ": " + str(len(tasks))


        


    def update(self, sge_command, token='job_info', sort_by_field='JB_job_number', reverse_order=True):
        '''Main function of derived model. Builds _data list from input.'''
        from operator import itemgetter
        self._tree = None
        self._dict = OrderedDict()
        self._data = []
        self._head = OrderedDict()
        try:
            self._tree = ElementTree.parse(os.popen(sge_command)).getroot()
            self._dict  = XmlDictConfig(self._tree)[token]
        except:
            #print self._dict
            pass

        # XmlDictConfig returns string instead of dict in case *_info are empty! Grrr...!
        if isinstance(self._dict, dict) and 'job_list' in self._dict.keys():
            d = self._dict['job_list']
            if isinstance(d, list):
                self._head = self._tag2idx(d[-1])
                self._data += [[x[key] for key in x.keys()] for x in d]
            elif isinstance(d, dict):
                self._head = self._tag2idx(d)
                self._data = [d.values()]
              
                # Sort list by specified header (given it's name, not index):
                if sort_by_field in self._head.values()  and len(self._data) > 0:
                    key_index = self.get_key_index(sort_by_field)
                    self._data = sorted(self._data,  key=itemgetter(key_index))
                    if reverse_order:
                        self._data.reverse()
                 
            


#################################################################
#               Tasks/Jobs History Table Model                  #
# It's different because data is taken in text format from      #
# the qacct output                                              #   
# ##############################################################

class JobsHistoryModel(QAbstractTableModel, SgeTableModelBase):
    def __init__(self,  parent=None, *args):
        super(self.__class__, self).__init__(parent)
      
    def update(self, sge_command, sort_by_field='jobnumber', reverse_order=True, rotate_by_field=None):
        '''Main function of derived model. Builds _data list from input.'''
        from operator import itemgetter
        self._dict = qccet_to_dict(os.popen(sge_command).read(), True)
        self._head = self._tag2idx(self._dict[self._dict.keys()[-1]])
        self._data = [self._dict[item].values() for item in self._dict]
        # Sort list by specified header (given it's name, not index):
        if sort_by_field in self._head.values():
            key_index = self.get_key_index(sort_by_field)
            self._data = sorted(self._data,  key=itemgetter(key_index))
            if reverse_order:
                self._data.reverse()



#################################################################
#               Machine Table Model                             #   
# ###############################################################

class MachineModel(QAbstractTableModel, MachineModelBase):
    def __init__(self,  parent=None, *args):
        super(self.__class__, self).__init__(parent)
        self._dict = OrderedDict()
        self._head = OrderedDict()
        self._data = []
      
    def update(self, sge_command, token='job_info', sort_by_field='hostname', reverse_order=False):
        '''Main function of derived model. Builds _data list from input.'''
        from operator import itemgetter
        self._data = []
        self._tree = ElementTree.parse(os.popen(sge_command))
        self._dict = OrderedDict()
        # Build a dictionary of dictionaries:
        # This differs again, because qhost -xml saves field's 
        # name as the attributes ('name') with values as values...
        for item in self._tree.findall('host'):
            name = item.attrib['name']
            if name == "global": continue
            self._dict[name] = OrderedDict()
            for x in item.getchildren():
                # hosts can have jobs attached to it.
                # Get rid of it for now.
                if not x.tag == 'job':
                    self._dict[name][x.attrib['name']] = x.text
                
        # Make a list of lists from that:
        self._head = self._tag2idx(self._dict[self._dict.keys()[-1]])
        self._data = [self._dict[item].values() for item in self._dict]
        # Sort list by specified header (given it's name, not index):
        if sort_by_field in self._head.values():
            key_index = self.get_key_index(sort_by_field)
            self._data = sorted(self._data,  key=itemgetter(key_index))
            if reverse_order:
                self._data.reverse()


##################################################################
#               Job Detail Table Model                           #
# This one is yet customized as it consists with many rows and   #
# two columns only (variable, value) TODO: replace with www rander#
# page with fine tuned artists friendly look../                  #   
# ################################################################


class JobDetailModel(QAbstractTableModel, SgeTableModelBase, CdbTableModel):
    def __init__(self, parent=None, *args):
        super(self.__class__, self).__init__(parent)
        self._dict = OrderedDict()
        self._head = OrderedDict()
        self._data = []
        self._tree = None
       
    def update(self, sge_command, sort_by_field="", reverse_order=False):
        from operator import itemgetter
        try:
            self._tree = ElementTree.parse(os.popen(sge_command)).getroot()
            self._dict  = XmlDictConfig(self._tree)['djob_info']['element']
        except:
            job_id = sge_command.split()[-1]
            self._dict = self.update_job_details_db(job_id)

        self._data  = []
        self._tasks = []
        self._data  = zip(self._dict.keys(), self._dict.values())
        self._head = self._tag2idx(self._dict)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        '''Headers builder. Note crude tokens replacement.'''
        # Replaces columns/rows names view custom tokens;
        def header_replace(name):
            if name in tokens.header.keys():
                name = tokens.header[name]
            return name
        # Nothing to do here:
        if role != Qt.DisplayRole:
            return QVariant()
        # Horizontal headers:
        if orientation == Qt.Horizontal and len(self._data):
            headers = ("Variable", "Value")
            return QVariant(headers[section])
            #return QVariant(header_replace(self._head[section]))
        # Vertical headers:
        if orientation == Qt.Vertical and len(self._data):
            if section in self._head:
                return QVariant(section)
                #return QVariant(header_replace(self._head[section]))
        return QVariant()

    def columnCount(self, parent):
        if len(self._data):
            return len(self._data[0])
        return 0




def test():
    import os
    tree = ElementTree.parse(os.popen('qstat -xml -u "*"'))
    root = tree.getroot()
    d    = XmlDictConfig(root)
    d    = JobsModel()
    d.update('qstat -xml -u "*"')
    print d.rowCount(None)
    print d.data(QModelIndex(0,2))



if __name__ == '__main__': main()

