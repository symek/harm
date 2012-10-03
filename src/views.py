#PyQt:
from PyQt4.QtCore  import *
from PyQt4.QtGui   import *

#Harm:
from SGEModels import *
from constants import *
import delegates
import models
import config

#System:
import os

class ViewConfig():
    def configure(self):
        # Prototype of config class.
        conf = config.Config()
        conf.load("src/harm.conf")
        if self.__class__.__name__ in conf.keys():
            c = conf[self.__class__.__name__]
            for item in c:
                self.__getattribute__(item[0])(item[1][0])
            
    def save_configure(self):
        pass


class ViewBase():
    def __init__(self):
        self.setSortingEnabled(True)
        self.setCornerButtonEnabled(True)
        self.setSelectionBehavior(1)
        self.setAlternatingRowColors(1)
        self.setDragDropMode(4)



class JobsView(QTableView, ViewBase, ViewConfig):
    def __init__(self, context):
        super(JobsView, self).__init__()
        self.context = context
        self.configure()

        # Models:
        self.model = models.JobsModel()
        self.model.update(SGE_JOBS_LIST_GROUPED)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setDynamicSortFilter(True)
        self.context.models['jobs_model'] = self.model
        self.context.models['jobs_proxy_model'] = self.proxy_model
        self.setModel(self.proxy_model)
        
        # Delegate:
        #self.jobs_delagate = delegates.JobsDelegate(self.context, self.model)
        #self.setItemDelegate(self.jobs_delagate)

        # Config:
        self.setColumnHidden(5, True)
        self.setColumnHidden(6, True)
        #self.horizontalHeader().setMovable(True)
        self.horizontalHeader().moveSection(7,0)
        
        # Clean:
        self.resizeColumnsToContents()
        self.resizeRowsToContents()


class TasksView(QTableView, ViewBase,ViewConfig):
    def __init__(self, context):
        super(self.__class__, self).__init__()
        self.context = context

        # Models:
        self.model = models.JobsModel()
        self.model.update(SGE_JOBS_LIST, 'queue_info')
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setDynamicSortFilter(True)
        self.context.models['tasks_model'] = self.model
        self.context.models['tasks_proxy_model'] = self.proxy_model
        self.setModel(self.proxy_model)

        # Clean:
        self.resizeColumnsToContents()
        self.resizeRowsToContents()


