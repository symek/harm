import sys
from time import time
from PyQt4.Qt import *

from PyQt4.QtCore  import *
from PyQt4.QtGui   import *

import tokens
import utilities
import views
import constants
import models

# Placeholder for future plugable backend
import slurm as backend

# Python 2.6 compatibility:
try:
    from collections import OrderedDict, defaultdict
except ImportError:
    from ordereddict import OrderedDict


class EditableProperties(dict):
    def __init__(self): 
        self['ArrayTaskThrottle'] = ('0',)
        self['Comment']     = ('',)
        self['Deadline']    = ('',)
        self['Dependency']  = ('',)
        self['ExcNodeList'] = ('',)
        self['ReqNodeList'] = ('',)
        self['Features']    = ('',)
        self['MinMemoryNode']  = ('14G',)
        self['MinTmpDiskNode'] = ('32G',)
        self['NumNodes']       = ('',)
        self['NumTasks']       = ('50',)
        self['Partition']      = ('3d', "cuda", "nuke")
        self['Priority']       = ('0',)
        self['ReservationName']= ('',)
        self['StartTime']      = ('',)
        self['TimeLimit']      = ('UNLIMITED',)
        self['OverSubscribe']  = ('yes', 'no', 'exclusive', 'force')

    def update_from_task(self, taskdict):
        for key in self.keys():
            if key in taskdict:
                self[key] = (taskdict[key],)

    def to_list(self):
        data = []
        for key in self.keys():
            data += [(key, self[key][0])]
        return data




class JobEditModel(QAbstractTableModel, models.HarmTableModel):
    def __init__(self, parent=None, *args):
        super(self.__class__, self).__init__(parent)
        self._dict = OrderedDict()
        self._head = OrderedDict()
        self._data = []
        self._tree = None
        self.changedItems = {}

    def setData(self, index, value, role):
        column = list(self._data[index.row()])
        column[index.column()] = str(value.toString())
        self._data[index.row()] = column
        header = self._head[index.row()]
        self.changedItems[header] = str(value.toString())
        print self.changedItems
        return True

       
    def update(self, jobid, taskid, sort_by_field="", reverse_order=False):
        def parse_slurm_output(output):
            properties = EditableProperties()
            out = output.split()
            data   = []
            header = []
            dict_  = OrderedDict()
            jobid_found = 0
            for item in out:
                var = item.split("=")
                name, var = var[0], ",".join(var[1:])
                if name == "JobId":
                    jobid_found += 1
                if jobid_found >1:
                    return data, header, dict_
                data   += [(name,var)]
                header += [name.strip()]
                dict_[name] = var
            return data, header, dict_

        from operator import itemgetter
        import subprocess
        if taskid:
            command = constants.SLURM_TASK_DETAILS.replace("<JOBID/>", jobid)
            command = command.replace("<TASKID/>", taskid)
        else:
            command = constants.SLURM_JOB_DETAILS.replace("<JOBID/>", jobid)

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
        if not out or err:
            return
        data, header, dict_ = parse_slurm_output(out)
        properties = EditableProperties()
        properties.update_from_task(dict_)
        self._data = properties.to_list()
        self._dict = properties
        for item in properties.keys():
            # if item in properties.keys():
            self._head[properties.keys().index(item)] = item
       

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


class JobEditView(QTableView):
    def __init__(self, model):
        super(self.__class__, self).__init__()
       
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setAlternatingRowColors(0)
        self.setModel(model)

        # Clean:
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.horizontalHeader().setResizeMode(3)


class JobEditWindow(QWidget):
    def __init__(self, jobid):
        QWidget.__init__(self)
        from models import JobDetailModel
        self.setGeometry(0,0, 600,750)
        self.setWindowTitle("Edit Job details")
        self.jobid = jobid
        self.model = JobEditModel()
        self.model.update(jobid, None)
        self.model.editable = True

        self.layout = QVBoxLayout(self)
        self.job_edit_view = JobEditView(self.model)
        self.layout.addWidget(self.job_edit_view)

        self.button = QPushButton('Reschedule', self)
        self.button.clicked.connect(self.reschedule)
        self.layout.addWidget(self.button)

    def reschedule(self):
        import subprocess
        command = backend.SLURM_UPDATE_JOB.replace("<JOBID/>", str(self.jobid))
        for key, value in self.model.changedItems.iteritems():
            command += " %s=%s" % (key, value) 
        print "Rescheduling job: %s" % self.jobid
        result = backend.reschedulehold_job([self.jobid])
        if result:
            print result
        out, err =subprocess.Popen(command, shell=True, \
        stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
        if out: 
            print out
        if err: 
            print err
        else:
            result = backend.unhold_job([self.jobid])

        if result:
            print result

        self.close()



