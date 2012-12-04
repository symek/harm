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
            return QVariant(header_replace(self._head[section]))
        # Vertical headers:
        elif orientation == Qt.Vertical and len(self._data):
            return QVariant(header_replace(int(section+1)))
        return QVariant()

    def parse_time_string(self, time):
        '''Parses the time string to reasonable format.'''
        date, time = time.split("T")
        return " ".join((time, date))



#################################################################
#               Database Table Model Base                       #
# This class enable minimal  databse support for sge models     #
# Current couchdb should be replaced by some abstraction layer! #
# ###############################################################


class CdbTableModel():
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
                self._data = d.values()
                # Sort list by specified header (given it's name, not index):
                if sort_by_field in self._head.values():
                    key_index = self.get_key_index(sort_by_field)
                    self._data = sorted(self._data,  key=itemgetter(key_index))
                    if reverse_order:
                        self._data.reverse()
            
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
# two columns only (variable, value) TODO: relace with www rander#
# page with fine tuned artists friendly look../                  #   
# ################################################################


class JobDetailModel(QAbstractTableModel, SgeTableModelBase):
    def __init__(self, parent=None, *args):
        super(self.__class__, self).__init__(parent)
        self._dict = OrderedDict()
        self._head = OrderedDict()
        self._data = []
        self._tree = None

    def update_db(self, job_id, sort_by_field="",  reverse_order=False):
        from couchdb import Server
        server = Server(os.getenv("CDB_SERVER"))
        db     = server['sge_db']
        map_   = ''' function(doc) { emit(doc._id, doc) } '''
        job    = db.query(map_, key=job_id).rows[0].value
        self._dict  = OrderedDict(job)
        self._head  = self._tag2idx(self._dict)
        self._tasks = []
        self._data  = zip(self._dict.keys(), self._dict.values())

    def update(self, sge_command, sort_by_field="", reverse_order=False):
        from operator import itemgetter
        self._tree = ElementTree.parse(os.popen(sge_command))
        self._tree = self._tree.find('djob_info')
        self._dict = OrderedDict()
        self._data = []
        self._tasks = []
        self.find_req(self._tree, self._data)
        self._tasks = self.find_task_details(self._tree)
        self._dict = OrderedDict(self._data)
        self._head = self._tag2idx(self._dict)

    def find_task_details(self, tree):
        def get_task_info(task):
            _list = []
            for item in task.getchildren():
                name  = item.find("UA_name")
                value = item.find("UA_value")
                _list.append((name.text, value.text))
            return _list

        def get_leaf(tree, leaf):
            leafs = []
            for ch in tree.getchildren():
                if ch.tag == leaf:
                    leafs.append(ch)
                else:
                    ch = get_leaf(ch, leaf)
                    if ch: leafs += ch
            return leafs

        tasks_details = []
        tasks_list = get_leaf(tree, "JB_ja_tasks")
        if not tasks_list: return []
        for sublist in tasks_list[0].getchildren():
            status = sublist.find("JAT_status")
            task_id= sublist.find("JAT_task_number")
            usage  = sublist.find("JAT_scaled_usage_list")
            if usage:
                usage = get_task_info(usage)
            tasks_details.append((status.text, task_id.text, usage))

        return tasks_details


    def find_req(self, tree, storage):
        children = tree.getchildren()
        for child in range(len(children)):
            if children[child].text:
                if len(children[child].text.strip()) == 0:
                    self.find_req(children[child], storage)
            elif not children[child].text:
                self.find_req(children[child], storage)
            if  children[child].text:
                if  children[child].tag in ("VA_variable", "UA_name"): 
                    tag  = children[child].text
                    text =  children[utilities.clamp(child+1, 0, len(children)-1)].text
                elif children[child].tag in ("VA_value", "UA_value"):
                    pass
                else: 
                    tag  = children[child].tag
                    text = children[child].text
                if len(text.strip()) > 0 and (tag, text.strip()) not in storage:
                    storage.append((tag, text.strip()))
        return storage

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

