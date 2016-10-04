from PyQt4.QtCore import *
import tokens
import utilities
import views
import slurm
import os
import constants
from time import time

# Python 2.6 compatibility:
try:
    from collections import OrderedDict, defaultdict
except ImportError:
    from ordereddict import OrderedDict


class HarmTableModel():
    """ Base model for tables based view. Currently Jobs View, Tasks View, Running View, 
        are using it. Main functinality is headers replacement, value conversion (str-> int), and
        DATA HOOKS which probably should be removed.

    """
    def __init__(self, parent=None):
        self.sge_view = parent
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
        '''This builds self._head dict {1:header, 2:another, ...}
        '''
        _map = OrderedDict()
        for x in range(len(item.keys())):
            _map[x] = item.keys()[x]
        return _map

    def data_hooks(self, index, value):
        '''Loops through all hook_* function of self, and executes it
           to preprocess data of a model. Hooks to be provided by derived classes
        '''
        for func in dir(self):
            if func.startswith("hook"):
                value = self.__getattribute__(func)(index, value)

        # Process data types: 
        if value == None: 
            return None
        elif isinstance(value, str):
            value = value.strip()
        if value.isdigit():
            return int(value)
        elif not value.isalpha():
            return float(value)
        elif not isinstance(value, str):
            return None 
        return value

    def get_key_index(self, key):
        '''Returns a key index in headers given its name.
        '''
        if key in self._head.values():
            return [k for k, v in self._head.iteritems() if v == key][0]
              
    def data(self, index, role):
        ''''Data access.
        '''
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()

        value  = None
        try:
            value = self._data[index.row()][index.column()]
            value = self.data_hooks(index, value)
        except:
            pass
        if not value: 
            return QVariant()    

        # Finally return something meaningfull:
        return QVariant(str(value))

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        '''Headers builder. Note crude tokens replacement.
        '''
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

    def parse_time_string(self, time, strip_date=True):
        '''Parses the time string to reasonable format.
        '''
        time = time.split("T")
        if len(time) == 2 and not strip_date:
            date, time = time
            return " ".join((time, date))
        return time[1]


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
#               Job Table Model                                 #   
# ###############################################################

class JobsModel(QAbstractTableModel, HarmTableModel):
    def __init__(self,  parent=None, *args):
        super(self.__class__, self).__init__(parent)
        self.sge_view = parent
        self._tree = None
        self._data = []
        self._head = OrderedDict()
        self._dict = OrderedDict()

    def update(self, length, reverse_order=True):
        '''Main function of derived model. Builds _data list from input.
        '''

        # All dirty data. We need to duplicate it here,
        # to keep things clean down the stream.
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        err = None

        # NOTE: Do we need this? 
        # Do't update too often:
        # if time() - self.last_update < 10:
            # return

        self.last_update = time()
        self._data = []
        self._dict = OrderedDict()
        self._head = OrderedDict()

        others, tmp     = slurm.get_notpending_jobs(None, True)
        # pending, header = slurm.get_pending_jobs(length, reverse_order=True)
        pending, header = slurm.get_current_jobs(length, reverse_order=True)
        # print pending
        # Two ways df dealing with it, because Slurm collapses only pending jobs, 
        # all others leaving expanded to tasks. 

        if pending:
            self._data = pending
            self._head = header
        # if others:
        #     # print others
        #     self._data += others
        #     self._head = header
        
        self.emit(SIGNAL("layoutChanged()"))


    # def hook_inprogres(self, index, value):
    #     """Changes panding to inprogress state for jobs which are already rendering.
    #     """
    #     column   = self._head[index.column()]
    #     time_idx = self.get_key_index('END_TIME')
    #     time     = self._data[index.column()][time_idx]
    #     if str(column.strip()) == 'STATE':
    #         if time != 'N/A':
    #             value = "rendering"
    #     return value





class TaskModel(QAbstractTableModel, HarmTableModel):
    '''Holds per task details of a job as retrieved from qstat -g d or database.
    '''
    def __init__(self,  parent=None, *args):
        super(self.__class__, self).__init__(parent)
        self.sge_view = parent
        self._tree = None
        self._data = []
        self._head = OrderedDict()


    def update(self, jobid=None, reverse_order=True):
        '''Main function of derived model. Builds _data list from input.
        '''
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
       
        if jobid: 
            command = constants.SLURM_JOBS_LIST.replace("<JOBID/>", jobid)
        else:
            command = constants.SLURM_RUNNING_JOBS_LIST

        try:
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

class RunningJobsModel(QAbstractTableModel, HarmTableModel):#, DBTableModel):
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

        try:
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
#               Job Table Model                                 #   
# ###############################################################

class HistoryModel(QAbstractTableModel, HarmTableModel):
    def __init__(self,  parent=None, *args):
        super(self.__class__, self).__init__(parent)
        self.sge_view = parent
        self._tree = None
        self._data = []
        self._head = OrderedDict()
        self._dict = OrderedDict()

    def update(self, user, reverse_order=True):
        '''Main function of derived model. Builds _data list from input.
        '''

        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        err = None

        self.last_update = time()
        self._data = []
        self._dict = OrderedDict()
        self._head = OrderedDict()

        data, header = slurm.get_accounted_jobs(user, reverse_order=True)
       
        if data:
            self._data = data
            self._head = header
        
        self.emit(SIGNAL("layoutChanged()"))


#################################################################
#               Machine Table Model                             #   
# ###############################################################

class MachineModel(QAbstractTableModel, HarmTableModel):
    def __init__(self,  parent=None, *args):
        super(self.__class__, self).__init__(parent)
        self._dict = OrderedDict()
        self._head = OrderedDict()
        self._data = []
      
    def update(self, reverse_order=False):
        '''Main function of derived model. Builds _data list from input.
        '''

        # All dirty data. We need to duplicate it here,
        # to keep things clean down the stream.
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        err = None

        self.last_update = time()
        self._data = []
        self._dict = OrderedDict()
        self._head = OrderedDict()

        history, header = slurm.get_nodes_info(None)
       
        if history:
            self._data = history
            self._head = header
        
        self.emit(SIGNAL("layoutChanged()"))



class JobDetailModel(QAbstractTableModel, HarmTableModel):
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
        command = constants.SLURM_JOB_DETAILS.replace("<JOBID/>", jobid)
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




if __name__ == '__main__': main()

