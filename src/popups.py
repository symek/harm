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
        self['Comment']     = ('',)
        self['ArrayTaskThrottle'] = ('0',)
        self['Dependency']  = ('',)
        self['ReqNodeList'] = ('',)
        self['ExcNodeList'] = ('',)
        self['Features']    = ('grafika', 'renders')
        self['MinMemoryNode']  = ('14G',)
        self['MinTmpDiskNode'] = ('32G',)
        self['Partition']      = ('3d', "cuda", "nuke")
        self['Priority']       = ('0',)
        self['ReservationName']= ('',)
        self['StartTime']      = ('',)
        self['TimeLimit']      = ('UNLIMITED',)

    def update_from_task(self, taskdict):
        for key in self.keys():
            if key in taskdict:
                self[key] = self[key] + (taskdict[key],)

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
        print "Property changed: %s" % str(self.changedItems)
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
        self.properties = EditableProperties()
        self.properties.update_from_task(dict_)
        self._data = self.properties.to_list()
        self._dict = self.properties
        for item in self.properties.keys():
            self._head[self.properties.keys().index(item)] = item
       

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
    def rowCount(self, parent):
        return len(self._data)


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
    def update_model(self, text):
        print "Hello world. %s" % str(text)

    def __init__(self, job_ids):
        QWidget.__init__(self)
        from models import JobDetailModel
        self.setGeometry(0,0, 340,550)
        # We may edit also selected tasks...
        assert(isinstance(job_ids, tuple) or isinstance(job_ids, list))
        self.job_ids_list = job_ids
        names = ",".join(self.job_ids_list)
        self.setWindowTitle("Warning: you are editing job: %s" % names)
        self.model = JobEditModel()
        self.model.update(self.job_ids_list[0], None)
        self.model.editable = True

        self.layout = QVBoxLayout(self)
        self.job_edit_view = JobEditView(self.model)

        # TODO update model from combo widget
        # for row in range(self.model.rowCount(None)):
        #     combo = QComboBox()
        #     combo.currentIndexChanged[str].connect(self.update_model)
        #     prop_name = self.model._data[row][0]
        #     combo.addItems(list(self.model.properties[prop_name]))
        #     index = self.model.index(row, 1)
        #     self.job_edit_view.setIndexWidget(index, combo)

        self.layout.addWidget(self.job_edit_view)
        self.button = QPushButton('Reschedule', self)
        self.button.clicked.connect(self.reschedule)
        self.layout.addWidget(self.button)

    def reschedule(self):
        import subprocess
        for jobid in self.job_ids_list:
            command = backend.SLURM_UPDATE_JOB.replace("<JOBID/>", str(jobid))
            for key, value in self.model.changedItems.iteritems():
                command += " %s=%s" % (key, value) 
            print "Rescheduling job: %s" % jobid
            result = backend.reschedulehold_job([jobid])
            if result:
                print result
            out, err =subprocess.Popen(command, shell=True, \
            stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
            if out: 
                print out
            if err: 
                print err
            else:
                result = backend.unhold_job([jobid])

            if result:
                print result

        self.close()



