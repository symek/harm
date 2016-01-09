from PyQt4.QtCore import *
import tokens
import utilities
import views
import os
from ordereddict import OrderedDict
# import couchdb as cdb
from constants import *
from time import time

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
            return len(self._data[0])
        return 0

    def build_header_dict(self, item):
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
            # print self._data[index.row()]
            # print self
            pass
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
        time = time.split("T")
        if len(time) == 2:
            date, time = time
            return " ".join((time, date))
        return time[0]

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
        if self._head[index.column()] in ('queue_name', 'hostname'):
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


# class DBTableModel():
#     '''Query jobs information from couchdb database. There is a single method
#     append_jobs_history which queries db using standard python couchdb module.
#     This class is meant to be inherited by other models like JobsModel.'''
#     _server = None
#     _db     = None
#     def connect_to_db(self, server_uri=None, db_name='sge_db'):
#         """Connects with default couchdb server taken from CDB_SERVER envvar.
#         Reads or creates sge_db database there. Thet are assign into self._server
#         and self._db local variables for later reuse.
#         """
#         if not server_uri:
#             server_uri = os.getenv("CDB_SERVER")
#         server = cdb.Server(server_uri)
#         assert server, "Can't do without couchdb server %s" % server_uri
#         self._server = server
#         if not db_name in server:
#             try:
#                 server.create(db_name)
#             except:
#                 print "Can't create database with a given name %s" % db_name
#                 return False

#         # self._db will be tested by actual get-data routines.
#         db = server[db_name]
#         if db:
#             self._db = db
#             return True

#     def get_jobs_db(self, job_count=150):
#         """Reads history from couchdb database. """
#         # A list of a jobs currently rendered or queued -
#         # (thus whose are tracked by SGE):
#         current_jobs = self._dict.keys()
#         # We need this!
#         if not self._db:
#             try: 
#                 self.connect_to_db()
#             except:
#                 return []
#         # This is our map function with hand crafted requests fields:
#         # It mimics qstat data, with a state replaced by 'cdb', which will allow us 
#         # to treat it differently down the stream.
#         map_   = '''function(doc) {
#             var js  = doc.JB_ja_structure.task_id_range;
#             var jss = "".concat(js.RN_min, "-", js.RN_max, ":", js.RN_step);
#             var que = doc.JB_hard_queue_list.destin_ident_list.QR_name;
#             emit(doc._id, [doc.JB_owner, "cdb", jss, doc.JB_priority, doc.JB_job_name, 
#                      "1", que, doc.JB_job_number, doc.JB_submission_time]);}'''
#         from time import time
#         t = time()
#         # FIXME: job_count should come from Config()
#         # WARNING: Newer couchdb changes 'count' for 'limit' afaik.
#         #query = self._db.query(map_, limit=job_count, descending=True).rows
#         query = self._db.view('harm/get_jobs_db', limit=job_count, descending=True).rows
#         if DEBUG:
#             print "DBTableModel.get_jobs_db:  " + str(time() -t)
#         # We need this because of unicode return in Windows:
#         query = [[str(y) for y in x.value] for x in query]

#         # Convert a time string and remove jobs which were
#         # returned by qstat:
#         for item in range(len(query)):
#             if query[item][-2] not in current_jobs:
#                 # FIXME: Instead of converting it to sge-ugly-string, we
#                 # should convert qstat query to epoc float, and convert it
#                 # in delegates!
#                 query[item][-1] = utilities.epoc_to_str_time(query[item][-1])
#             else:
#                 query.remove(item)
#         # Merge cdb with qstat:
#         return query

#     def get_job_details_db(self, job_id, sort_by_field="",  reverse_order=False):
#         """Retrieves the entire documenet (job) from database."""
#         from structured import dict2et
#         from time import time
#         if not self._db:
#             try: self.connect_to_db()
#             except: return OrderedDict()
#         t   = time()
#         job = self._db.get(job_id, OrderedDict())
#         if DEBUG:
#             print "DBTableModel.get_job_details_db: %s " % str(time() - t)
#         return job

#     def get_tasks_db(self, job_id):
#         """Calls get_tasks_db permenent view from couchdb. This function by default
#         returns all fields from JAT_scaled_usage_list sublist.
#         """
#         from time import time
#         if not self._db:
#             try: self.connect_to_db()
#             except: return OrderedDict()
#         t = time()
#         job = self._db.view('harm/get_tasks_db', key=job_id).rows
#         if DEBUG:
#             print "DBTableModel.get_tasks_db: %s" % str(time()-t)
#         return job




#################################################################
#               Machine Table Model Base                        #
# The only difference is headerData which takes machine name as #
# the row name.                                                 #
# ###############################################################
class MachineModelBase(SgeTableModelBase):
    def __init__(self, parnet=None):
        super(self.__class__, self).__init__(parent)


    # def headerData(self, section, orientation, role=Qt.DisplayRole):
    #     '''Headers builder. Note crude tokens replacement.'''
    #     # Replaces columns/rows names view custom tokens;
    #     def header_replace(name):
    #         if name in tokens.header.keys():
    #             name = tokens.header[name]
    #         return name
    #     # Nothing to do here:
    #     if role != Qt.DisplayRole:
    #         return QVariant()
    #     # Horizontal headers:
    #     if orientation == Qt.Horizontal and len(self._data):
    #         return QVariant(header_replace(self._head[section]))
    #     # Vertical headers:
    #     elif orientation == Qt.Vertical and len(self._data):
    #         return QVariant(section)
    #         # return QVariant(header_replace(self._dict.keys()[section]))
    #     return QVariant()



#################################################################
#               Job Table Model                                 #   
# ###############################################################

class JobsModel(QAbstractTableModel, SgeTableModelBase): #DBTableModel):
    def __init__(self,  parent=None, *args):
        super(self.__class__, self).__init__(parent)
        self.sge_view = parent
        self._tree = None
        self._data = []
        self._head = OrderedDict()
        self._dict = OrderedDict()

    def append_jobs_history(self, history_length):
        '''Appends history jobs from a database (using DBTableModel.get_jobs_db()) '''
        pass
        # query = self.get_jobs_db(history_length)
        # from time import time
        # t = time()
        # self._data += query
        # # FIXME!
        # # This has to be (?) hard coded here, as we don't retrieve fields' names
        # # from a database atm. This is unfortunate, since general rule here is creating everything on the fly, 
        # # It's not properly tested though...
        # # If not headers yet:
        # if len(self._head) == 0:
        #     self._head = OrderedDict({0:"JB_owner", 1:"state", 2:"tasks", 3:"JAT_prio", 4:"JB_name", 5:"slots", \
        #                   6:"queue_name", 7:"JB_job_number", 8:"JB_submission_time"})
        # if DEBUG:
        #     print "JobsModel.append_jobs_history: " + str(time() - t)

    def parse_slurm_output(self, output):

        lines = output.split("\n")
        if len(lines) == 1: lines  += [""]
        head, lines = lines[0], lines[1:]
        head = [word.strip() for word in head.split()]
        lines = [line.split() for line in lines if line]
        return lines, head


    def update(self, sge_command, token='job_info', sort_by_field='JB_job_number', reverse_order=True):
        '''Main function of derived model. Builds _data list from input.'''
        from operator import itemgetter
        import subprocess
        # All dirty data. We need to duplicate it here,
        # to keep things clean down the stream.
        err = None
        t = time()
        self._data = []
        self._dict = OrderedDict()
        self._head = OrderedDict()
        # ElementTree raise an exeption on xml parse error:\
        try:
            command = sge_command
            out, err =subprocess.Popen(command, shell=True, \
            stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
            if out:
                data, header = self.parse_slurm_output(out)
                self._data = data
                for item in header:
                    self._head[header.index(item)] = item
        except: 
            print "Counld't get scheduler info."
            print err




#################################################################
#               Tasks Table Model                               #   
# ###############################################################

class TaskModel(QAbstractTableModel, SgeTableModelBase):#, DBTableModel):
    '''Holds per task details of a job as retrieved from qstat -g d or database.'''
    def __init__(self,  parent=None, *args):
        super(self.__class__, self).__init__(parent)
        self.sge_view = parent
        self._tree = None
        self._data = []
        self._head = OrderedDict()

    # def update_db(self, job_id, token=""):
    #     """Reads tasks info from a database record (JB_ja_tasks.ulong_sublist field)
    #     by quering permanent view harm/get_tasks_db. Additionally some standard fields
    #     are added manually at front (jobid, owner, tasks).
    #     """
    #     # Cancel previous data:
    #     self._head = OrderedDict()
    #     self._data = []

    #     # Get tasks info from db:
    #     self.emit(SIGNAL("layoutAboutToBeChanged()"))
    #     tasks = self.get_tasks_db(job_id)

    #     # Empty query happens for whatever reasons:
    #     if tasks: tasks = tasks[0].value
    #     else: return

    #     # FIXME: This should not be necessery. 
    #     longest = max([len(t) for t in tasks])

    #     # Iterate over tasks
    #     for task in tasks:
    #         _data = [None]*longest
    #         #_data = [None for item in task]
    #         for item in task:
    #             name, value = item
    #             if name not in self._head.values(): 
    #                 field_idx = len(self._head) 
    #                 self._head[field_idx] = name
    #             else:
    #                 field_idx = self._head.values().index(name)
    #             assert field_idx < len(_data), "field_idx exeeds _data length."
    #             # FIXME: on Windows value is unicode, not str, we have to force it here
    #             # so PyQt4 displays it properly. This probably should be fixed differently
    #             _data[field_idx] = str(value)
    #         self._data.append(_data)
    #     self.emit(SIGNAL("layoutChanged()"))




    def update(self, sge_command, token='job_info', sort_by_field='JB_job_number', reverse_order=True):
        '''Main function of derived model. Builds _data list from input.'''
        def parse_slurm_output(output):
            lines = output.split("\n")
            if len(lines) == 1: lines  += [""]
            head, lines = lines[0], lines[1:]
            head = [word.strip() for word in head.split()]
            lines = [line.split() for line in lines if line]
            return lines, head

        from operator import itemgetter
        import subprocess
        # All dirty data. We need to duplicate it here,
        # to keep things clean down the stream.
        err = None
        t = time()
        self._data = []
        self._dict = OrderedDict()
        self._head = OrderedDict()
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        # ElementTree raise an exeption on xml parse error:\
        try:
            command = sge_command
            out, err =subprocess.Popen(command, shell=True, \
            stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
            if out:
                data, header = parse_slurm_output(out)
                self._data = data
                for item in header:
                    self._head[header.index(item)] = item
        except: 
            print "Counld't get scheduler info."
            print err
        self.emit(SIGNAL("layoutChanged()"))

    # def update(self, sge_command, token='queue_info', sort_by_field='JB_job_number', reverse_order=True):
    #     """Updates model from qstata commandline tool. First we take an xml output, parse with ET,
    #     then build a dictionary (OrderedDict) out of it, then build self._data [[jobinfo], ...] and 
    #     self._head: dict(1:header, 2: header, ...).

    #     It is a subject of change. Data handling should be done by external object,
    #     DataHandler(), this class should expect native Python as input and accomodate it to its model. 
    #     """
    #     from operator import itemgetter
    #     # Cancel data:
    #     self._tree = None
    #     self._dict = OrderedDict()
    #     self._data = []
    #     self._head = OrderedDict()
    #     self.emit(SIGNAL("layoutAboutToBeChanged()"))

    #     # Get new one:
    #     try:
    #         self._tree = ElementTree.parse(os.popen(sge_command)).getroot()
    #         self._dict  = XmlDictConfig(self._tree)[token]
    #     except:
    #         pass

    #     # XmlDictConfig returns string instead of dict in case *_info are empty!
    #     if isinstance(self._dict, dict) and 'job_list' in self._dict.keys():
    #         d = self._dict['job_list']
    #         if isinstance(d, list):
    #             self._head = self.build_header_dict(d[-1])
    #             self._data += [[x[key] for key in x.keys()] for x in d]
    #         elif isinstance(d, dict):
    #             self._head = self.build_header_dict(d)
    #             self._data = [d.values()]
    #             # Sort list by specified header (given it's name, not index):
    #             if sort_by_field in self._head.values()  and len(self._data) > 0:
    #                 key_index = self.get_key_index(sort_by_field)
    #                 self._data = sorted(self._data,  key=itemgetter(key_index))
    #                 if reverse_order:
    #                     self._data.reverse()

    #     # End of updating:
    #     self.emit(SIGNAL("layoutChanged()"))

    def hook_cputime(self, index, value):
        """Translate cpu time in seconds into 00:00:00 string."""
        from datetime import timedelta
        column = self._head[index.column()]
        if column in ('cpu', 'ru_wallclock'):
            if value: 
                value = int(float(value))
                # FIXME: Hard coded cores number:
                # if column == 'cpu': value /= 8
                value = str(timedelta(seconds=value))
        return value

    def hook_sge_time(self, index, value):
        """Translates time related SGE fields in ugly format  "%H:%M:%S %d-%m-%Y"
        into something hopefully nicer.
        """
        if self._head[index.column()] in ('submission_time', "start_time", "end_time", "qsub_time", "SUBMIT_TIME"):
            if isinstance(value, float):
                value = utilities.epoc_to_str_time(float(value), "%H:%M:%S %d-%m-%Y")
            elif len(value.split()) == 5 and ":" in value:
                value = value.split()[3]
        return value

    def hook_mem_usage(self, index, value):
        import time
        if self._head[index.column()] in ('mem',):
            value = str(float(value)/10000.0)[0:4] + " GB"
        return value

    def columnCount(self, parent):
        """This reimplements SgeTableModelBase.columnCount since self._data won't tell us 
        (in case of tasks details) columns count, because database entires can vary per row.
        """
        if len(self._data):
            return len(self._head)
        return 0

          
# RUNNIG JOBS MODEL

class RunningJobsModel(QAbstractTableModel, SgeTableModelBase):#, DBTableModel):
    '''Holds per task details of a job as retrieved from qstat -g d or database.'''
    def __init__(self,  parent=None, *args):
        super(self.__class__, self).__init__(parent)
        self.sge_view = parent
        self._tree = None
        self._data = []
        self._head = OrderedDict()



    def update(self, command, token='job_info', sort_by_field='JB_job_number', reverse_order=True):
        '''Main function of derived model. Builds _data list from input.'''
        def parse_slurm_output(output):
            lines = output.split("\n")
            if len(lines) == 1: lines  += [""]
            head, lines = lines[0], lines[1:]
            head = [word.strip() for word in head.split()]
            lines = [line.split() for line in lines if line]
            return lines, head

        from operator import itemgetter
        import subprocess
        # All dirty data. We need to duplicate it here,
        # to keep things clean down the stream.
        err = None
        t = time()
        self._data = []
        self._dict = OrderedDict()
        self._head = OrderedDict()
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        # ElementTree raise an exeption on xml parse error:\
        try:
            # command = sge_command
            out, err =subprocess.Popen(command, shell=True, \
            stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
            if out:
                data, header = parse_slurm_output(out)
                self._data = data
                for item in header:
                    self._head[header.index(item)] = item
        except: 
            print "Counld't get scheduler info."
            print err
        self.emit(SIGNAL("layoutChanged()"))




#################################################################
#               Tasks/Jobs History Table Model                  #
# It's different because data is taken in text format from      #
# the qacct output                                              #   
# ##############################################################

# class JobsHistoryModel(QAbstractTableModel, SgeTableModelBase):
#     def __init__(self,  parent=None, *args):
#         super(self.__class__, self).__init__(parent)
      
#     def update(self, sge_command, sort_by_field='jobnumber', reverse_order=True, rotate_by_field=None):
#         '''Main function of derived model. Builds _data list from input.'''
#         from operator import itemgetter
#         self._dict = qccet_to_dict(os.popen(sge_command).read(), True)
#         self._head = self.build_header_dict(self._dict[self._dict.keys()[-1]])
#         self._data = [self._dict[item].values() for item in self._dict]
#         # Sort list by specified header (given it's name, not index):
#         if sort_by_field in self._head.values():
#             key_index = self.get_key_index(sort_by_field)
#             self._data = sorted(self._data,  key=itemgetter(key_index))
#             if reverse_order:
#                 self._data.reverse()



#################################################################
#               Machine Table Model                             #   
# ###############################################################

class MachineModel(QAbstractTableModel, MachineModelBase):
    def __init__(self,  parent=None, *args):
        super(self.__class__, self).__init__(parent)
        self._dict = OrderedDict()
        self._head = OrderedDict()
        self._data = []
      
    def update(self, command, token='job_info', sort_by_field='hostname', reverse_order=False):
        '''Main function of derived model. Builds _data list from input.
        '''
        def parse_slurm_output(output):
            nodes = output.split("\n\n")
            data   = []
            header = []
            dict_  = OrderedDict()
            hostname= ""
            build_header = True

            for node in nodes:
                items = node.split()[:-1]
                line = []
                d_   = OrderedDict()
                for item in items:
                    var = item.split("=")
                    name, var = var[0], ",".join(var[1:])
                    if name == 'NodeName':
                        hostname = var
                    line += [var]
                    if build_header:
                        header += [name.strip()]
                    d_[name] = var
                data.append(line)
                dict_[hostname] = d_
                build_header = False

            return data, header, dict_

        from operator import itemgetter
        import subprocess
        self._tree = None
        self._data = []
        self._dict = OrderedDict()
      
        # ElementTree raise an exeption on xml parse error:\
        # try:
            # command = sge_command
        out, err =subprocess.Popen(command, shell=True, \
        stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
        if out:
            data, header, dict_ = parse_slurm_output(out)
            self._data = data
            self._dict = dict_
            for item in header:
                self._head[header.index(item)] = item
       
            if reverse_order:
                self._data.reverse()


##################################################################
#               Job Detail Table Model                           #
# This one is yet customized as it consists with many rows and   #
# two columns only (variable, value) TODO: replace with www rander#
# page with fine tuned artists friendly look../                  #   
# ################################################################


class JobDetailModel(QAbstractTableModel, SgeTableModelBase):# DBTableModel):
    def __init__(self, parent=None, *args):
        super(self.__class__, self).__init__(parent)
        self._dict = OrderedDict()
        self._head = OrderedDict()
        self._data = []
        self._tree = None
       
    def update(self, jobid, taskid, sort_by_field="", reverse_order=False):
        def parse_slurm_output(output):
            out = output.split()
            data   = []
            header = []
            dict_  = OrderedDict()
            for item in out:
                var = item.split("=")
                name, var = var[0], ",".join(var[1:])
                data   += [(name,var)]
                header += [name.strip()]
                dict_[name] = var
            return data, header, dict_

        from operator import itemgetter
        import subprocess
        command = SLURM_JOB_DETAILS.replace("<JOBID/>", jobid)
        command = command.replace("<TASKID/>", taskid)
        # All dirty data. We need to duplicate it here,
        # to keep things clean down the stream.
        err = None
        t = time()
        self._data = []
        self._dict = OrderedDict()
        self._head = OrderedDict()
        # ElementTree raise an exeption on xml parse error:\
        # try:
            # command = sge_command
        out, err =subprocess.Popen(command, shell=True, \
        stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
        if out:
            data, header, dict_ = parse_slurm_output(out)
            self._data = data
            self._dict = dict_
            for item in header:
                self._head[header.index(item)] = item
        # except: 
            # print "Counld't get scheduler info."
            # print err
        #     self._tree = ElementTree.parse(os.popen(sge_command)).getroot()
        #     self._dict  = XmlDictConfig(self._tree)['djob_info']['element']
        # except:
        #     job_id = sge_command.split()[-1]
        #     self._dict = self.get_job_details_db(job_id)
        #     #print "JB_submission_time: " + str("JB_submission_time" in self._dict)

        # self._data  = []
        # self._tasks = []
        # self._data  = zip(self._dict.keys(), self._dict.values())
        # self._head = self.build_header_dict(self._dict)

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

