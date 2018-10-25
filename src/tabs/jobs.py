#PyQt4:
from PyQt4.QtGui import QTableView, QSortFilterProxyModel, QItemDelegate
from PyQt4.QtGui import QWidget, QVBoxLayout, QMenu, QApplication
from PyQt4.QtGui import QBrush, QPen, QColor, QStyle, QLinearGradient
from PyQt4.QtCore import Qt, QAbstractTableModel, SIGNAL
# Own
from views import ViewBase
from plugin import PluginManager, PluginType
from menus import ContextMenuBase
import models
import delegates
import utilities

from collections import OrderedDict, defaultdict

class JobsPlugin(PluginManager):

    name = "Jobs"
    type = PluginType.LeftTab
    autoupdate = True

    def start(self, parent):
        """ Entry point to a plugin functionality
        """
        window = utilities.get_main_window()
        self.tab = Tab(parent)
        parent.jobs_tab = self.tab
        parent.jobs_view = self.tab.jobs_view
        window.connect(self.tab.jobs_view, SIGNAL("clicked(const QModelIndex&)"),  
            self.jobs_view_clicked)

    def update(self):
        self.tab.jobs_view.update_model()

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
        # self.job_detail_basic_view_update(job_id)
        # self.job_detail_view.update_model(job_id, None)

class Tab(QWidget):
    def __init__(self, parent):
        super(Tab, self).__init__(parent)
        parent.addTab(self, "Queue Jobs")
        self._vboxlayout = QVBoxLayout(self)
        self.jobs_view = View(self)
        self._vboxlayout.addWidget(self.jobs_view)
        self.tasks_view = TasksView()
        self._vboxlayout.addWidget(self.tasks_view)
  

class View(QTableView, ViewBase):
    def __init__(self, parent):
        super(self.__class__, self).__init__(parent)
        
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


    def openContextMenu(self, position):
        '''Context menu entry.'''
        self.context_menu = ContextMenu(self, self.mapToGlobal(position))


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
            self._data  = window.server.get_key('jobs')
            self._head  = window.server.get_key('jobs_header')
            self.emit(SIGNAL("layoutChanged()"))


class TasksView(QTableView, ViewBase):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setEditTriggers(self.NoEditTriggers)
        self.configure()
        self.setAlternatingRowColors(0)

        # Models:
        self.model = TaskModel(self)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setDynamicSortFilter(True)
        self.setModel(self.proxy_model)

        # Clean:
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def openContextMenu(self, position):
        self.context_menu = menus.TasksContextMenu(self.context, self.mapToGlobal(position))


class TaskModel(QAbstractTableModel, models.HarmTableModel):
    '''Holds per task details of a job as retrieved from qstat -g d or database.
    '''
    def __init__(self,  parent=None, *args):
        super(self.__class__, self).__init__(parent)
        self._tree = None
        self._data = []
        self._head = OrderedDict()


    def update(self, jobid):
        '''Main function of derived model. Builds _data list from input.
        '''
        import slurm as backend
        if not jobid:
            return
            
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self._data = []
        self._dict = OrderedDict()
        self._head = OrderedDict()
        _data, _head = backend.get_job_tasks(jobid)

        if not _data:
            return

        self._data = _data
        self._head = _head

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


class ContextMenu(QMenu, ContextMenuBase):
    def __init__(self, parent, position):
        super(self.__class__, self).__init__()
        self.view    = parent.views['jobs_view']
        self.model   = context.models['jobs_model']
        self.app     = context.app
        self.context = context
        items = [x for x in dir(self) if x.startswith('callback_')]
        self.item_list = ['callback_hold',
                          'callback_unhold',
                          "",
                          'callback_reschedule',
                          "",
                          'callback_edit',
                          "",
                          'callback_show_sequence',
                          "",
                          'callback_cancel',]

        self.bind_actions(self.build_action_strings(self.item_list))
        self.execute(position)


    def callback_hold(self):
        """ Calls hold command of bakend for a selected job's id.
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.hold_job(jobs)
        self.context.GUI.message("\n".join(result))

    def callback_unhold(self):
        """ Calls unhold command of bakend for a selected job's id.
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.unhold_job(jobs)
        self.context.GUI.message("\n".join(result))

    def callback_suspend(self):
        """ Suspend jobs.
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.suspend_job(jobs)
        self.context.GUI.message("\n".join(result))

    def callback_resume(self):
        """ Resume jobs (unsuspend).
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.resume_job(jobs)
        self.context.GUI.message("\n".join(result))

    def callback_reschedule(self):
        """ Reschedule jobs.
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.reschedule_job(jobs)
        self.context.GUI.message("\n".join(result))

    def callback_cancel(self):
        """ Cancel jobs.
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.cancel_job(jobs)
        self.context.GUI.message("\n".join(result))

    def callback_edit(self):
        """ Edit jobs.
        """
        from popups import JobEditWindow
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        if jobs:
            self.window = JobEditWindow(jobs)
            self.window.show()


    def callback_copy_to_nuke(self):
        """Creates a Nuke's paste string to create ReadNodes from 
        selected render jobs.
        """
        indices = self.view.selectedIndexes()
        indices = [self.view.proxy_model.mapToSource(index) for index in indices]
        job_ids = list(set([index.row() for index in indices]))
        job_id_index = self.model.get_key_index('JB_job_number')
        clipboard    = self.app.clipboard()
        read  = []; nuke_paste_in = ""
        model = self.context.views['job_detail_view'].model
        for index in indices:
            job_id  = self.model._data[index.row()][job_id_index]
            if job_id not in read: 
                model.update(constants.SGE_JOB_DETAILS % job_id)
                picture = model.get_value('OUTPUT_PICTURE')
                rn_min  = model.get_value("RN_min")[0]
                rn_max  = model.get_value('RN_max')[0]
                read.append(job_id)
                if picture:
                   p0 = utilities.padding(picture[0], 'nuke')[0]
                   nuke_paste_in += constants.NUKE_READ_NODE_STRING % (p0, rn_min, rn_max)
                   nuke_paste_in += "\n"
        clipboard.setText(nuke_paste_in)

    def callback_show_sequence(self):
        import subprocess
        hafarm_parms = self.context.GUI.get_job_parms_from_detail_view()
        picture_parm = hafarm_parms[u'parms'][u'output_picture']
        picture_info = utilities.padding(picture_parm, format="shell")
        picture_path = picture_info[0] 

        config = self.context.config
        viewer = config.select_optional_executable('image_viewer')

        if viewer:
            # Hard coded fix for rv :(
            if viewer.endswith("rv"):
                picture_path = picture_path.replace("*", "#")    
            command = [viewer, picture_path]
            subprocess.Popen(command, shell=False)
            return
        else: 
            self.context.GUI.message("Can't find viewer app in PATH. Trying RV in rez subshell...")

        package = ['rv']
        command = "export HOME=%s; export DISPLAY=:0; rv %s" % (os.getenv("HOME"), picture_path.replace("*", "#"))
        pid = utilities.run_rez_shell(command, package)
        if pid:
            return
