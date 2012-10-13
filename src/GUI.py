# System:
import os, sys, time

#PyQt4:
from PyQt4.QtCore  import *
from PyQt4.QtGui   import * 
from PyQt4         import QtGui

# Harm models:
from SGEModels import *
from contextMenus import *
from mwcallbacks import HarmMainWindowCallbacks

# Harm utilities & settings:
import tokens, delegates, txt2xml
import structured, utilities, views
from constants import *

#Google charts:
from pygooglechart import *

# FIXME Is it the right place?
class Context(object):
    def __init__(self):
        self.models = {}
        self.menues = {}
        self.views  = {}

context = Context()
    

        

class HarmMainWindowGUI(HarmMainWindowCallbacks):
    def setupGUI(self,  init):

        # Main Tabs:
        self.statusBar()
        self.left_tab_widget   = QtGui.QTabWidget()
        self.right_tab_widget  = QtGui.QTabWidget()

        context.splashMessage = self.splashMessage
        self.splashMessage("Setup Jobs Tabs...")
        self.setupJobsTab()
        #self.splashMessage("Setup History Tab...")
        #self.setupHistoryTab() 
        self.splashMessage("Setup Machines Tab...")
        self.setupMachinesTab()
        self.splashMessage("Setup Task Detail Tab...")
        self.setupJobDetailTab()
        self.splashMessage("Setup Stdout and stderr Tabs...")
        self.setupTaskStdTab()
        #self.splashMessage("Setup Statistics Tab...")
        #self.setupStatisticsTab()

        # Docks? (do we need them here):
        dock_left = QtGui.QDockWidget(self)
        dock_left.setWidget(self.left_tab_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_left)
        dock_right = QtGui.QDockWidget(self)
        dock_right.setWidget(self.right_tab_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock_right)

        # Toolbar:
        self.toolbar = self.addToolBar('Main')
        self.refreshAction = QtGui.QAction(QtGui.QIcon('/STUDIO/scripts/harm/icons/refresh.png'), 'Refresh', self)
        self.refreshAction.setShortcut('Ctrl+R')
        self.refreshAction.setStatusTip('Refresh jobs and task view from SGE.')
        self.toolbar.addAction(self.refreshAction)  

  

    def setupJobsTab(self):
        '''List of tasks waiting for the execution and currently proccesed (in task view).
           Should have also list of recently finished jobs.'''
        # Tab Setup:
        self.jobs_tab         = QtGui.QWidget()
        jobs_tab_vbox         = QtGui.QVBoxLayout(self.jobs_tab)
        self.left_tab_widget.addTab(self.jobs_tab, "Jobs")

         # Filter:
        self.jobs_filter_label = QtGui.QLabel()
        self.jobs_filter_label.setText("Jobs filter")
        jobs_filter_hbox = QtGui.QHBoxLayout()
        jobs_filter_hbox.addWidget(self.jobs_filter_label)
        self.jobs_filter_line = QLineEdit()
        jobs_filter_hbox.addWidget(self.jobs_filter_line)
        jobs_tab_vbox.insertLayout(0, jobs_filter_hbox)

        # Jobs models (Left Tabs):
        xml = os.popen(SGE_JOBS_LIST_GROUPED)
        self.jobs_model = SGETableModel(xml, ["job_info"])
        self.jobs_proxy_model = QSortFilterProxyModel()
        self.jobs_proxy_model.setSourceModel(self.jobs_model)
        self.jobs_proxy_model.setDynamicSortFilter(True)
        #context.models['jobs_model'] = self.jobs_model
        #context.models['jobs_proxy_model'] = self.jobs_proxy_model
    
        # History filters:
        #self.jobs_filter_menu = QtGui.QMenu()
        #self.jobs_filter_presets = QtGui.QMenu('Presets')
        #self.jobs_filter_presets.addAction(QString("owner"))
        #self.jobs_filter_menu.addMenu(self.jobs_filter_presets)
        #jobs_filter_hbox.addWidget(self.jobs_filter_menu)

        # Jobs View:
        self.jobs_view = views.JobsView(context)
        jobs_tab_vbox.addWidget(self.jobs_view)

        # Tasks view Controls:
        self.tasks_onlySelected_toggle = QtGui.QCheckBox()
        self.tasks_onlySelected_toggle.setText("Show Only Selected Jobs")
        tasks_controls = QtGui.QHBoxLayout()
        tasks_controls.addWidget(self.tasks_onlySelected_toggle)

        # Tasks View (Left Tabs):
        self.tasks_view = views.TasksView(context)
        jobs_tab_vbox.insertLayout(2, tasks_controls)
        jobs_tab_vbox.addWidget(self.tasks_view)

    def setupHistoryTab(self):
        '''Historical jobs aquaured from qacct SGE utility. Heavy post-process
           has to be undertaken here. '''
        # History View:
        self.history_view = views.HistoryView(context)
        #self.history_view = views.JobsTreeHistoryView(context)
        self.history_tab   = QtGui.QWidget()
        self.left_tab_widget.addTab(self.history_tab, "History")
        history_tab_vbox = QtGui.QVBoxLayout(self.history_tab)
        history_tab_vbox.addWidget(self.history_view)
        
    def setupMachinesTab(self):
        '''Current status of a renderfarm as presented by qhost.'''
        #Machines (Left Tabs):
        self.machine_tab   = QtGui.QWidget()
        self.machine_view = views.MachineView(context)
        context.views['machine_view'] = self.machine_view
       
        # Combo box for job views:
        self.machine_view_combo   = QtGui.QComboBox()
        self.machine_view_combo.addItems(['List View','Tree View'])

        self.left_tab_widget.addTab(self.machine_tab, "Machines")
        machine_tab_vbox = QtGui.QVBoxLayout(self.machine_tab)
        machine_tab_vbox.addWidget(self.machine_view_combo)
        machine_tab_vbox.addWidget(self.machine_view)

        # Tree machine view setup:
        #self.machine_tree_view = SGETreeView2(os.popen(SGE_CLUSTER_LIST))
        #self.machine_tree_view.setItemDelegate(self.machines_delagate)
        #machine_tab_vbox.addWidget(self.machine_tree_view)
        #self.machine_tree_view.setAlternatingRowColors(1)
        #self.machine_tree_view.hide()

    def setupJobDetailTab(self):
        '''Presents details of particular job (selected in either Jobs or Tasks View).
           This is specially treaky. I'm Considering of using WebKit and render this data
           as a HTML.'''
        # Task details view (Right Tabs):
        self.job_detail_tab  = QtGui.QWidget()
        self.right_tab_widget.addTab(self.job_detail_tab, "Job Details")
        job_detail_tab_vbox  = QtGui.QVBoxLayout(self.job_detail_tab)

        # Combo box for job views:
        #self.job_view_combo   = QtGui.QComboBox()
        #self.job_view_combo.addItems(['List View','Detailed View'])
        #job_tab_vbox.addWidget(self.job_view_combo)

        # Filter:
        '''self.job_details_filter_label = QtGui.QLabel()
        self.job_details_filter_label.setText("Variable filter")
        job_details_hbox = QtGui.QHBoxLayout()
        job_details_hbox.addWidget(self.job_details_filter_label)
        self.job_details_filter_line = QLineEdit()
        job_details_hbox.addWidget(self.job_details_filter_line)
        job_details_hbox.addWidget(self.job_view_combo)
        job_tab_vbox.insertLayout(0, job_details_hbox)'''

        self.job_detail_view = views.JobDetailView(context)
        job_detail_tab_vbox.addWidget(self.job_detail_view)

        # Tree job view setup:
        #if job_id:
        #    self.job_tree_view = SGETreeView(os.popen(SGE_JOB_DETAILS % job_id))
        #else:
        #    self.job_tree_view = SGETreeView(os.popen(EMPTY_SGE_JOB_DETAILS))

        #job_tab_vbox.addWidget(self.job_tree_view)
        #self.job_tree_view.setAlternatingRowColors(1)
        #self.job_tree_view.hide()


    def setupTaskStdTab(self):
        '''Task Stdout/err reads log files given task details'''
        # Stdout view (Right Tabs):
        self.stdout_tab = QtGui.QWidget()
        self.right_tab_widget.addTab(self.stdout_tab, "Stdout")
        stdout_tab_vbox  = QtGui.QVBoxLayout(self.stdout_tab)
        self.stdout_view = QtGui.QTextBrowser(self.stdout_tab)
        stdout_tab_vbox.addWidget(self.stdout_view)
        self.stdout_view.setPlainText(str("No stdout yet."))

        # Stderr view (Right Tabs):
        self.stderr_tab = QtGui.QWidget()
        self.right_tab_widget.addTab(self.stderr_tab, "Stderr")
        stderr_tab_vbox  = QtGui.QVBoxLayout(self.stderr_tab)
        self.stderr_view = QtGui.QTextBrowser(self.stderr_tab)
        stderr_tab_vbox.addWidget(self.stderr_view)
        self.stderr_view.setPlainText(str("No stderr yet."))


    def setupStatisticsTab(self):
        '''Statistics of particular job.'''
        # Setup Stat Tab:
        self.stat_tab = QtGui.QWidget()
        self.right_tab_widget.addTab(self.stat_tab, "Statistics")
        self.stat_tab_vbox = QtGui.QVBoxLayout(self.stat_tab)

        # In case jobs_model was empty:
        try:
            job_id = self.jobs_model.root[0][0].text
            f = os.popen(SGE_HISTORY_JOB % job_id).read()
        except:
            f = os.popen(SGE_HISTORY_JOB_LAST).read()

        f = txt2xml.parse_text(f, True)
        xml = structured.dict2et(f, "job_info")
        
        self.stat_model = SGETableModel(None, ["job_info"])
        self.stat_model.setTree(xml)
        self.stat_proxy_model = QSortFilterProxyModel()
        self.stat_proxy_model.setSourceModel(self.stat_model)
        stat_tab_size = QSize(self.stat_tab.width()/3, self.stat_tab.height())

        # Wallclock bars:
        self.wallclock_bars = QChart(self.stat_tab, GroupedVerticalBarChart, size=stat_tab_size)
        self.wallclock_bars.name='wallclock'
        self.wallclock_bars.set_title("Render time.")
        self.stat_tab_vbox.addWidget(self.wallclock_bars)

        # Wallclock bars:
        self.ram_bars = QChart(self.stat_tab, GroupedVerticalBarChart, size=stat_tab_size)
        self.ram_bars.name='ram'
        self.ram_bars.set_colours(['0080FF'])
        self.ram_bars.set_title("Ram usage.")
        self.stat_tab_vbox.addWidget(self.ram_bars)
        
        # I/O bars:
        self.io_bars = QChart(self.stat_tab, GroupedVerticalBarChart, size=stat_tab_size)
        self.io_bars.name='io'
        self.io_bars.set_legend(("Read", "Write"))
        self.io_bars.set_colours(['00ff00', 'ff0000'])
        self.io_bars.set_title("I/O blocks.")
        self.stat_tab_vbox.addWidget(self.io_bars)
         
  
        






