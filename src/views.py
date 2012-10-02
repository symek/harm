#PyQt:
from PyQt4.QtCore  import *
from PyQt4.QtGui   import *

#Harm:
from SGEModels import *
from constants import *
import delegates
import models

#System:
import os

class ViewConfig():
    pass


class ViewBase():
    pass



class JobsView(ViewBase, ViewConfig, QTableView):
    def __init__(self, context):
        super(JobsView, self).__init__()
        self.context = context
        # Basic config
        # TODO: Move into ViewConfig:

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
        
        self.setSortingEnabled(True)
        self.setCornerButtonEnabled(True)
        self.setSelectionBehavior(1)
        self.setAlternatingRowColors(1)
        self.setDragDropMode(4)

        # Clean:
        self.resizeColumnsToContents()
        self.resizeRowsToContents()


