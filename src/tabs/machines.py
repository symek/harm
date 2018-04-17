#PyQt4:
from PyQt4.QtGui import QTableView, QSortFilterProxyModel, QItemDelegate
from PyQt4.QtGui import QWidget, QVBoxLayout, QApplication
from PyQt4.QtGui import QBrush, QPen, QColor, QStyle, QLinearGradient
from PyQt4.QtCore import Qt, QAbstractTableModel, SIGNAL
# Own
from views import ViewBase
from plugin import PluginManager, PluginType
import models
import delegates
import utilities

from collections import OrderedDict, defaultdict

class MachinesPlugin(PluginManager):
    name = "Machines"
    type = PluginType.LeftTab
    autoupdate = True
    def start(self, parent):
        self.tab = Tab(parent)
        parent.machine_tab = self.tab
        parent.machine_view = self.tab.machine_view

    def update(self):
        self.tab.machine_view.update_model()

    def register_signals(self):
        return True

class Tab(QWidget):
    def __init__(self, parent):
        super(Tab, self).__init__(parent)
        parent.addTab(self, "Machines")
        self._vboxlayout = QVBoxLayout(self)
        self.machine_view = View(parent)
        self._vboxlayout.addWidget(self.machine_view)
     
class View(QTableView, ViewBase):
    def __init__(self, parent):
        super(self.__class__, self).__init__(parent)
        # Ugly
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openContextMenu)
        self.configure()
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

         # Delegate:
        self.delagate = MachinesDelegate(self)
        self.setItemDelegate(self.delagate)

    def openContextMenu(self, position): 
        pass
        #self.context_menu = TasksContextMenu(self.context, self.mapToGlobal(position))


class Model(QAbstractTableModel, models.HarmTableModel):
    def __init__(self,  server=None):
        super(self.__class__, self).__init__()
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
        #Ugly
        window = utilities.get_main_window()
        if hasattr(window, "server"):
            self.emit(SIGNAL("layoutAboutToBeChanged()"))
            self._data  = window.server.output_dict['nodes']
            self._head  = window.server.output_dict['nodes_header']
            self.emit(SIGNAL("layoutChanged()"))


class MachinesDelegate(QItemDelegate):
    def __init__(self, parent):
        QItemDelegate.__init__(self, parent)
        self.parent = parent
       

    def paint(self, painter, option, index):
        painter.save()
        # # set background color
        painter.setPen(QPen(Qt.NoPen))

        # # Get RAM information:
        s_index      = self.parent.proxy_model.mapToSource(index)
        mem_used_idx = self.parent.model.get_key_index("AllocMem")
        mem_free_idx = self.parent.model.get_key_index("FreeMem")
        mem_real_idx = self.parent.model.get_key_index("RealMemory")

        mem_used = self.parent.model._data[s_index.row()][mem_used_idx]
        mem_free = self.parent.model._data[s_index.row()][mem_free_idx]
        mem_real = self.parent.model._data[s_index.row()][mem_real_idx]

        if mem_used.isdigit(): mem_used = int(mem_used)
        else: mem_used = 0
        if mem_real.isdigit(): mem_real = int(mem_real)
        else:     mem_real = 0
        
        # # Set color based on ram and load:
        # # TODO: Color setting should come from confing file or user condiguration!
        if mem_used and mem_real:
            color = QColor()
            sat = utilities.clamp(mem_used/mem_real, 0.0, 1.0)
            sat = utilities.fit(sat, 0.0, 1.0, 0.1, 0.85)
            hue = 1.0 #utilities.clamp(load_avg/num_proc, 0.0, 1.0)
            hue = utilities.fit(hue, 0.0, 1.0, .25, .9)
            color.setHsvF(hue, sat , 1)
            # Mark in red hosts with used ram above 0.9 (or other SGE_HOST_RAM_WARNING constant)
            # if mem_used > mem_real * constants.SGE_HOST_RAM_WARNING:
            #     color.setHsvF(1, 1 , 1)
            painter.setBrush(QBrush(color))

        # # Set selection color:
        if option.state & QStyle.State_Selected:
            painter.setBrush(QBrush(Qt.gray))
        painter.drawRect(option.rect)

        painter.setPen(QPen(Qt.gray))
        value = index.data(Qt.DisplayRole)
        if value.isValid():
            text = value.toString()
            painter.drawText(option.rect, Qt.AlignLeft, text)

        painter.restore()
