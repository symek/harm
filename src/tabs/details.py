#PyQt4:
from PyQt4.QtGui import QTableView, QSortFilterProxyModel, QItemDelegate, QSplitter
from PyQt4.QtGui import QWidget, QVBoxLayout, QMenu, QApplication, QLineEdit
from PyQt4.QtGui import QBrush, QPen, QColor, QStyle, QLinearGradient, QTextBrowser
from PyQt4.QtCore import Qt, QAbstractTableModel, SIGNAL
# Own
from views import ViewBase
from plugin import PluginManager, PluginType
from menus import ContextMenuBase
import models
import delegates
import utilities

from collections import OrderedDict, defaultdict

import logging


###############################################################
#     Job Detail Table View                                      #
###############################################################



class JobsPlugin(PluginManager):

    name = "DetailsTabPlugin"
    type = PluginType.RightTab
    autoupdate = True

    def start(self, parent):
        """ Entry point to a plugin functionality
        """
        window = utilities.get_main_window()
        self.tab = Tab(parent)
        # parent.details_tab  = self.tab
        # parent.details_view = self.tab.details_view
        # window.connect(self.tab.details_view, SIGNAL("clicked(const QModelIndex&)"),  
            # self.jobs_view_clicked)

    def update(self):
        self.tab.detail_view.update_model()

    def register_signals(self):
        return True

    def jobs_view_clicked(self, index):
        '''Calls for selecting job on Jobs View.
        '''
        s_index      = self.tab.jobs_view.proxy_model.mapToSource(index)
        job_id_index = self.tab.jobs_view.model.get_key_index("ARRAY_JOB_ID")
        state_index  = self.tab.jobs_view.model.get_key_index("STATE")
        job_id       = self.tab.jobs_view.model._data[s_index.row()][job_id_index]
        state        = self.tab.jobs_view.model._data[s_index.row()][state_index]
        self.tab.tasks_view.update_model(job_id)
        

class Tab(QWidget):
    def __init__(self, parent):
        super(Tab, self).__init__(parent)
        logger = logging.getLogger("Details")
        logger.info("Starting...")  
        parent.addTab(self, "Details")
        self._vboxlayout = QVBoxLayout(self)
        self.job_detail_basic_view = QTextBrowser(self)
        self._vboxlayout.addWidget(self.job_detail_basic_view)
        details_tab_splitter = QSplitter(self)
        details_tab_splitter.setOrientation(Qt.Vertical)
        self._vboxlayout.addWidget(details_tab_splitter)
        self.detail_view = DetailView(self)
        self._vboxlayout.addWidget(self.detail_view)
  
class DetailView(QTableView, ViewBase):
    def __init__(self, parent):
        super(self.__class__, self).__init__(parent)
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setAlternatingRowColors(0)

        # Models:
        self.model = Model()
        self.model.update()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setDynamicSortFilter(True)
        self.setModel(self.proxy_model)

        # Clean:
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def update_model(self, *arg):
        '''Overwrites update_model() to allow append history jobs to a model.'''
        self.model.reset()
        self.model.update(*arg)
        # Clean:
        self.resizeColumnsToContents()
        self.resizeRowsToContents()




class Model(QAbstractTableModel, models.HarmTableModel):
    def __init__(self,  parent=None, server=None):
        super(self.__class__, self).__init__(parent)
        self.server = server
        self._dict = OrderedDict()
        self._head = OrderedDict()
        self._data = []
        self.BG_BRUSH = self.create_gradient_brush()

    def create_gradient_brush(self):
        horGradient = QLinearGradient(0, 0, 100, 0)
        verGradient = QLinearGradient(0, 0, 0, 20)
        gradient = verGradient 
        gradient.setColorAt(0.0, QColor("black"))
        gradient.setColorAt(1.0, QColor("grey"))
        brush = QBrush(gradient)
        return brush
      
    def update(self, reverse_order=False):
        '''Main function of derived model. Builds _data list from input.
        '''
        window = utilities.get_main_window()
        if hasattr(window, "server"):
            self.emit(SIGNAL("layoutAboutToBeChanged()"))
            self._data  = window.server.get_by_key('jobs')
            self._head  = window.server.get_by_key('jobs_header')
            self.emit(SIGNAL("layoutChanged()"))




