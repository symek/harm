# System:
import os, sys, time

#PyQt4:
from PyQt4.QtCore  import *
from PyQt4.QtGui   import * 
from PyQt4         import QtGui

# Harm models:
from SGEModels import *
from contextMenus import *

# Harm utilities & settings:
import tokens, delegates, txt2xml
import structured, utilities
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
    
class HarmMainWindowCallbacks():
    '''Holds only callbacks on various Qt Sigmals inside a main window.'''
    def refreshAll(self):
        self.jobs_model.reset()
        self.jobs_model.update(os.popen(SGE_JOBS_LIST_GROUPED))
        self.tasks_model.reset()
        self.tasks_model.update(os.popen(SGE_JOBS_LIST_GROUPED))
        self.machine_model.reset()
        self.machine_model.update(os.popen(SGE_CLUSTER_LIST))
        self.machine_model.reduce("host")
        self.jobs_view.resizeRowsToContents()
        self.tasks_view.resizeRowsToContents()
        self.machine_view.resizeRowsToContents()

    def jobs_view_clicked(self, indices):
        '''Calls for selecting job on Jobs View.'''
        self.update_job_model_from_jobs(indices)
        self.set_tasks_proxy_model_filter(0)
        job_id = self.jobs_model.root[indices.row()][0].text
        self.update_stat_view(job_id)

    
    def tasks_view_clicked(self, indices):
        '''Calls for selecting job on Task View.'''
        self.update_job_model_from_tasks(indices)
        job_id = self.tasks_model.root[indices.row()][0].text
        self.update_stat_view(job_id)
        #self.update_image_view(job_id)
    
    def finished_view_clicked(self, indices):
        '''Calls for selecting job on Task View.'''
        tm = {}
        for index in range(len(self.finished_model.root[0])):
            tm[self.finished_model.root[0][index].tag] = index
        job_id = self.finished_model.root[indices.row()][tm['jobnumber']].text
        self.update_stat_view(job_id)
           

    def update_job_model_from_jobs(self, indices):
        '''Update job detialed view on selection in Jobs view.'''
        job_id  = self.jobs_model.root[indices.row()][0].text
        command = SGE_JOB_DETAILS % job_id
        self.job_model.update(os.popen(command))
        self.job_view.reset()

    def update_job_model_from_tasks(self, indices):
        '''Update job detialed view in seleciton in Tasks view.'''
        tagidx = utilities.tag2idx(self.tasks_model.root[0])
        job_id = self.tasks_model.root[indices.row()][tagidx['JB_job_number']].text
        task_id= self.tasks_model.root[indices.row()][tagidx['tasks']].text
        command = SGE_JOB_DETAILS % job_id
        self.update_std_views(self.right_tab_widget.currentIndex())

        if self.job_view_combo.currentIndex() == 0:
            self.job_model.update(os.popen(command))
            self.job_view.reset()
        else:
            self.job_tree_view.update(os.popen(command))
            #self.job_tree_view.populate(self.job_tree_view.root)
            #print self.job_tree_view.data.find("OUTPUT_PICTURE").text


    def update_std_views(self, tab_index):
        '''Read from disk logs specified by selected tasks..'''
        index  = self.tasks_view.currentIndex()
        # TODO: 0 and -1 are problemetic. Should we have 
        # a index map for tables?
        try:
            job_id = self.tasks_model.root[index.row()][0].text
            task_id= self.tasks_model.root[index.row()][-1].text
        except:
            return

        # Stdout Tab:
        if tab_index == 1: # If second tab selected            
            element = self.job_model.root[0]
            stdout_path = element.find("JB_stdout_path_list")[0].find("PN_path").text
            job_name    = element.find("JB_job_name").text
            stdout_path += job_name + ".o" + job_id + "." + task_id
            try: 
                stdout_file  = open(stdout_path, 'r')
                self.stdout_view.setPlainText(stdout_file.read())
                stdout_file.close()
            except: pass

        # Stderr Tab:
        elif tab_index == 2:
            element = self.job_model.root[0]
            stderr_path = element.find("JB_stdout_path_list")[0].find("PN_path").text
            job_name    = element.find("JB_job_name").text
            stderr_path += job_name + ".e" + job_id + "." + task_id
            try: 
                stderr_file  = open(stderr_path, 'r')
                self.stderr_view.setPlainText(stderr_file.read())
                stderr_file.close()
            except: pass

    '''def update_image_view(self, job_id):
        if self.right_tab_widget.currentIndex() != 4:
            return
        tagidx = utilities.tag2idx(self.tasks_model.root[0])
        job_id = self.tasks_model.root[indices.row()][tagidx['JB_job_number']].text
        task_id= self.tasks_model.root[indices.row()][tagidx['tasks']].text
        command = SGE_JOB_DETAILS % job_id
        self.update_std_views(self.right_tab_widget.currentIndex())
        self.job_model.update(os.popen(command))
        self.job_view.reset()
    context = self.job_model.root[0].find("JB_context")[0]
        for value in range(len(context)):
            if context[value].text == "OUTPUT_PICTURE":
                image = context[value+1].text
                print image'''

    def change_job_view(self, view):
        '''Switch job view between table and tree views.'''
        if view == 0:
            self.job_tree_view.hide()
            self.job_view.show()     
        else:
            self.job_view.hide()
            self.job_tree_view.show()

    def change_machine_view(self, view):
        '''Switch machines view between table and tree views.'''
        if view == 0:
            self.machine_tree_view.hide()
            self.machine_view.show()     
        else:
            self.machine_view.hide()
            self.machine_tree_view.show()

    '''def set_job_detail_proxy_model_wildcard(self, wildcard):
        wildcard = wildcard.split(":")
        self.job_detail_proxy_model.setFilterWildcard(wildcard[-1])
        self.job_detail_tree_view.resizeRowsToContents() '''
        

    def set_jobs_proxy_model_wildcard(self, wildcard):
        '''Sets a filter for jobs view according to user input in jobs_filter_line'''
        wildcard = wildcard.split(":")
        self.jobs_proxy_model.setFilterWildcard(wildcard[-1])
        self.jobs_view.resizeRowsToContents()
        if len(wildcard) > 1:
            for x in range(len(self.jobs_model.root[0])):
                tag = str(self.jobs_model.root[0][x].tag)
                if tag in tokens.header.keys():
                    column_name = tokens.header[tag]
                    if str(wildcard[0]).lower() == column_name.lower():
                        self.jobs_proxy_model.setFilterKeyColumn(x)
                        break


    def set_tasks_proxy_model_filter(self, int):
        '''Sets a filter according to job selection in jobs view.'''
        if self.tasks_onlySelected_toggle.isChecked():
            index  = self.jobs_view.currentIndex()
            job_id = self.jobs_model.root[index.row()][0].text
            self.tasks_proxy_model.setFilterWildcard(job_id)
        else:
            self.tasks_proxy_model.setFilterWildcard("")
        self.tasks_view.resizeRowsToContents()


    def update_stat_view(self, job_id):
        '''Retrieve statistics from qaccel for current job selection (jobs view)'''
        import math
        if self.right_tab_widget.currentIndex() == 3:
            f = os.popen(SGE_HISTORY_JOB % job_id).read()
            f = txt2xml.parse_text(f, True)
            xml = structured.dict2et(f, "job_info")
            self.stat_model.setTree(xml)

            # Any items?            
            if not len(self.stat_model.root): 
                print "No %s found in history" % job_id
                return

            # Stats data retrieving and processing:
            tagidx   = utilities.tag2idx(self.stat_model.root[0])
            times    = [float(item[tagidx['ru_wallclock']].text) for item in self.stat_model.root]
            vmem     = [item[tagidx['maxvmem']].text for item in self.stat_model.root]
            in_block = [float(item[tagidx['ru_inblock']].text) for item in self.stat_model.root]
            ou_block = [float(item[tagidx['ru_oublock']].text) for item in self.stat_model.root]
            tasks =    [math.trunc(float(item[tagidx['taskid']].text)) for item in self.stat_model.root]
            
            # Normalize _vmem to Gbytes:
            _vmem = []
            for item in vmem:
                value, size = (float(item[:-1]), item[-1])
                if size == "M": value /= 1000.0
                _vmem.append(value)
            vmem = _vmem
          
            # Update wallclock_bar widget:
            _max = max(times)
            _min = min(times)
            stat_tab_size = QSize(self.stat_tab.width(), self.stat_tab.height()/3)
            self.wallclock_bars.resize(stat_tab_size)
            self.wallclock_bars.set_title("Render time. (jobid: %s)" % job_id)
            self.wallclock_bars.height = self.stat_tab.height()/3
            self.wallclock_bars.width  = self.stat_tab.width()
            self.wallclock_bars.data = []
            self.wallclock_bars.add_data(times)
            self.wallclock_bars.set_bar_width(self.wallclock_bars.width / (len(times)))
            self.wallclock_bars.set_bar_spacing(0)
            self.wallclock_bars.set_group_spacing(1)
            self.wallclock_bars.axis = []
            self.wallclock_bars.set_axis_labels('x', tasks)
            self.wallclock_bars.set_axis_labels('y', ["%s min." % math.trunc(x) for x in (0.0, _max/60)])
            self.wallclock_bars.download()
            self.wallclock_bars.update()

             # Update ram_bar widget:
            _max = max(vmem)
            _min = min(vmem)
            self.ram_bars.resize(stat_tab_size)
            self.ram_bars.set_title("Ram usage. (jobid: %s)" % job_id)
            self.ram_bars.height = self.stat_tab.height()/3
            self.ram_bars.width  = self.stat_tab.width()
            self.ram_bars.data = []
            self.ram_bars.add_data(vmem)
            self.ram_bars.set_bar_width(self.ram_bars.width / (len(times)))
            self.ram_bars.set_bar_spacing(0)
            self.ram_bars.set_group_spacing(1)
            self.ram_bars.axis = []
            self.ram_bars.set_axis_labels('x', tasks)
            self.ram_bars.set_axis_labels('y', ["%sG" % x for x in (0.0, _max)])
            self.ram_bars.download()
            self.ram_bars.update()
            
             # Update io_bar widget:
            self.io_bars.resize(stat_tab_size)
            self.io_bars.set_title("I/O blocks.  (jobid: %s)" % job_id)
            self.io_bars.height = self.stat_tab.height()/3
            self.io_bars.width  = self.stat_tab.width()
            self.io_bars.set_bar_spacing(0)
            self.io_bars.set_group_spacing(1)
            self.io_bars.data = []
            self.wallclock_bars.set_group_spacing(0)
            self.io_bars.add_data(in_block)
            self.io_bars.add_data(ou_block)
            self.io_bars.set_bar_width(self.io_bars.width / (len(times)*2.5))
            self.io_bars.axis = []
            self.io_bars.set_axis_labels('x', tasks)
            self.io_bars.set_axis_labels('y', ["%s MB" % math.trunc(x*4/1024) for x in [0.0, max(in_block+ou_block)]])
            self.io_bars.download()
            self.io_bars.update()

    def openJobsMenu(self, position):
        self.jobs_menu = JobsContextMenu(context, self.jobs_view.mapToGlobal(position))
        context.menues['jobs_menu'] = self.jobs_menu

    def openTasksMenu(self, position):
        self.tasks_menu = TasksContextMenu(context, self.tasks_view.mapToGlobal(position))
        

class HarmMainWindowGUI(HarmMainWindowCallbacks):
    def setupGUI(self,  init):
        # GUI:
        # TODO: Make Tabs plugable - allowing easy extensions
        # of Harm (like: Render Manager / File brower / Render browser etc)

        # Main Tabs:
        self.statusBar()
        self.splashMessage("Setup Left Tabs...")
        self.setupLeftTabs(init)
        self.splashMessage("Setup Right Tabs...")
        self.setupRightTabs(init)

        # Docks? (do we need them here):
        dock_left = QtGui.QDockWidget(self.tr('Jobs'), self)
        dock_left.setWidget(self.left_tab_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_left)
        dock_right = QtGui.QDockWidget(self.tr('Details'), self)
        dock_right.setWidget(self.right_tab_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock_right)

        # Toolbar:
        self.toolbar = self.addToolBar('Main')
        self.refreshAction = QtGui.QAction(QtGui.QIcon('../icons/refresh.png'), 'Refresh', self)
        self.refreshAction.setShortcut('Ctrl+R')
        self.refreshAction.setStatusTip('Refresh jobs and task view from SGE.')
        self.toolbar.addAction(self.refreshAction)  

    def setupLeftTabs(self, init):
        self.splashMessage("Setup Jobs Tabs...")
        self.setupJobsTab(1)
        self.splashMessage("Setup Finished Tabs...")
        self.setupFinishedTab(1) 
        self.splashMessage("Setup Machines Tabs...")
        self.setupMachinesTab(1)


    def setupJobsTab(self, init):
        # Tab Setup:
        self.left_tab_widget  = QtGui.QTabWidget()
        self.jobs_tab    = QtGui.QWidget()
        jobs_tab_vbox   = QtGui.QVBoxLayout(self.jobs_tab)
        self.left_tab_widget.addTab(self.jobs_tab, "Jobs")

        # Jobs models (Left Tabs):
        xml = os.popen(SGE_JOBS_LIST_GROUPED)
        self.jobs_model = SGETableModel(xml, ["job_info"])
        self.jobs_proxy_model = QSortFilterProxyModel()
        self.jobs_proxy_model.setSourceModel(self.jobs_model)
        self.jobs_proxy_model.setDynamicSortFilter(True)
        context.models['jobs_model'] = self.jobs_model
        context.models['jobs_proxy_model'] = self.jobs_proxy_model
    
        # Filter:
        self.jobs_filter_label = QtGui.QLabel()
        self.jobs_filter_label.setText("Jobs filter")
        jobs_filter_hbox = QtGui.QHBoxLayout()
        jobs_filter_hbox.addWidget(self.jobs_filter_label)
        self.jobs_filter_line = QLineEdit()
        jobs_filter_hbox.addWidget(self.jobs_filter_line)
        jobs_tab_vbox.insertLayout(0, jobs_filter_hbox)

        # History filters:
        #self.jobs_filter_menu = QtGui.QMenu()
        #self.jobs_filter_presets = QtGui.QMenu('Presets')
        #self.jobs_filter_presets.addAction(QString("owner"))
        #self.jobs_filter_menu.addMenu(self.jobs_filter_presets)
        #jobs_filter_hbox.addWidget(self.jobs_filter_menu)
        

        # Jobs View:
        self.jobs_view = QTableView()
        context.views['jobs_view'] = self.jobs_view
        self.jobs_delagate = delegates.JobsDelegate(context, self.jobs_model)
        self.jobs_view.setItemDelegate(self.jobs_delagate)
        self.jobs_view.setSortingEnabled(True)
        self.jobs_view.setCornerButtonEnabled(True)
        self.jobs_view.setSelectionBehavior(1)
        #self.jobs_view.setAlternatingRowColors(1)
        self.jobs_view.setModel(self.jobs_proxy_model)
        self.jobs_view.resizeColumnsToContents()
        self.jobs_view.resizeRowsToContents()
        jobs_tab_vbox.addWidget(self.jobs_view)
        #Context menu:
        self.jobs_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.jobs_view.customContextMenuRequested.connect(self.openJobsMenu)

        # Tasks view Controls:
        self.tasks_onlySelected_toggle = QtGui.QCheckBox()
        self.tasks_onlySelected_toggle.setText("Show Only Selected Jobs")
        tasks_controls = QtGui.QHBoxLayout()
        tasks_controls.addWidget(self.tasks_onlySelected_toggle)

        # Tasks View (Left Tabs):
        xml = os.popen(SGE_JOBS_LIST)
        self.tasks_model = SGETableModel(xml, ["queue_info"])
        # TODO: Globally register models and views?
        context.models['tasks_model'] = self.tasks_model
        # Proxy model:
        self.tasks_proxy_model = QSortFilterProxyModel()
        self.tasks_proxy_model.setSourceModel(self.tasks_model)
        self.tasks_proxy_model.setDynamicSortFilter(True)
        context.models['tasks_proxy_model'] = self.tasks_proxy_model
        # View:
        self.tasks_view = QTableView()
        #self.tasks_delagate = delegates.TasksDelegate(context, self.tasks_model)
        #self.tasks_view.setItemDelegate(self.tasks_delagate)
        self.tasks_view.setSortingEnabled(True)
        self.tasks_view.setSelectionBehavior(1)
        #self.tasks_view.setAlternatingRowColors(1)
        self.tasks_view.sortByColumn(9,0)
        self.tasks_view.setModel(self.tasks_proxy_model)
        self.tasks_view.resizeColumnsToContents()
        self.tasks_view.resizeRowsToContents()
        context.views['tasks_view'] = self.tasks_view
        jobs_tab_vbox.insertLayout(2, tasks_controls)
        jobs_tab_vbox.addWidget(self.tasks_view)
        #Context menu
        self.tasks_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tasks_view.customContextMenuRequested.connect(self.openTasksMenu)

    def setupFinishedTab(self, init):
        # Finished jobs:
        f = os.popen(SGE_HISTORY_LIST).read()
        self.splashMessage("Parsing history file...")
        f = txt2xml.parse_text(f)
        self.splashMessage("History to XML...")
        xml = structured.dict2et(f, "job_info")
        self.finished_model = SGETableModel(None, ['job_info'])
        context.models['finished_model'] = self.finished_model
        self.finished_proxy_model = QSortFilterProxyModel()
        self.finished_proxy_model.setSourceModel(self.finished_model)
        self.finished_model.setTree(xml)
        self.finished_view  = QTableView()
        self.finished_view.setSortingEnabled(True)
        self.finished_tab   = QtGui.QWidget()
        self.finished_view.setSelectionBehavior(1)
        self.finished_view.setAlternatingRowColors(1)
        self.finished_view.setModel(self.finished_proxy_model)
        self.finished_view.resizeColumnsToContents()
        self.finished_view.resizeRowsToContents()
        self.left_tab_widget.addTab(self.finished_tab, "Finished")
        finished_tab_vbox = QtGui.QVBoxLayout(self.finished_tab)
        finished_tab_vbox.addWidget(self.finished_view)
        
    def setupMachinesTab(self, init):
        #Machines (Left Tabs):
        self.machine_model = SGETableModel(os.popen(SGE_CLUSTER_LIST), ["qhost"], None, True)
        self.machine_proxy_model = QSortFilterProxyModel()
        self.machine_proxy_model.setSourceModel(self.machine_model)
        self.machine_proxy_model.setDynamicSortFilter(True)
        self.machine_model.reduce("host")
        self.machine_view  = QTableView()
        context.views['machine_view'] = self.machine_view
        self.machine_tab   = QtGui.QWidget()

        # Combo box for job views:
        self.machine_view_combo   = QtGui.QComboBox()
        self.machine_view_combo.addItems(['List View','Tree View'])

        # Machines view cdn...
        #print utilities.tag2idx(self.machine_model.root[0], True)
        self.machines_delagate = delegates.MachinesDelegate(self.machine_model)
        self.machine_view.setItemDelegate(self.machines_delagate)
        self.machine_view.setSortingEnabled(True)
        self.machine_view.setSelectionBehavior(1)
        self.machine_view.setAlternatingRowColors(1)
        self.machine_view.setModel(self.machine_proxy_model)
        self.machine_view.resizeColumnsToContents()
        self.machine_view.resizeRowsToContents()
        self.left_tab_widget.addTab(self.machine_tab, "Machines")
        machine_tab_vbox = QtGui.QVBoxLayout(self.machine_tab)
        machine_tab_vbox.addWidget(self.machine_view_combo)
        machine_tab_vbox.addWidget(self.machine_view)

         # Tree machine view setup:
        self.machine_tree_view = SGETreeView2(os.popen(SGE_CLUSTER_LIST))
        #self.machine_tree_view.setItemDelegate(self.machines_delagate)
        machine_tab_vbox.addWidget(self.machine_tree_view)
        self.machine_tree_view.setAlternatingRowColors(1)
        self.machine_tree_view.hide()

    def setupRightTabs(self, init):
        # Task details view (Right Tabs):
        # Right tab setup:
        self.right_tab_widget = QtGui.QTabWidget()
        self.job_tab          = QtGui.QWidget()
        self.right_tab_widget.addTab(self.job_tab, "Task Details")
        job_tab_vbox          = QtGui.QVBoxLayout(self.job_tab)

        # Combo box for job views:
        self.job_view_combo   = QtGui.QComboBox()
        self.job_view_combo.addItems(['List View','Detailed View'])
        job_tab_vbox.addWidget(self.job_view_combo)

        # Filter:
        '''self.job_details_filter_label = QtGui.QLabel()
        self.job_details_filter_label.setText("Variable filter")
        job_details_hbox = QtGui.QHBoxLayout()
        job_details_hbox.addWidget(self.job_details_filter_label)
        self.job_details_filter_line = QLineEdit()
        job_details_hbox.addWidget(self.job_details_filter_line)
        job_details_hbox.addWidget(self.job_view_combo)
        job_tab_vbox.insertLayout(0, job_details_hbox)'''

        # Table job view setup:
        job_id = None
        self.job_model = SGEListModel2(None, "djob_info")
        if len(self.jobs_model.root):
            job_id = self.jobs_model.root[0][0].text
            self.job_model.update(os.popen(SGE_JOB_DETAILS % job_id))
        else:
            self.job_model.update(os.popen(EMPTY_SGE_JOB_DETAILS))

        self.job_view = QTableView()
        #self.job_delagate = delegates.JobDelegate(context, self.job_model)
        #self.job_view.setItemDelegate(self.job_delagate)
        self.job_view.setSelectionBehavior(1)
        self.job_view.setModel(self.job_model)
        self.job_view.resizeColumnsToContents()
        self.job_view.resizeRowsToContents()
        job_tab_vbox.addWidget(self.job_view)

        # Tree job view setup:
        if job_id:
            self.job_tree_view = SGETreeView(os.popen(SGE_JOB_DETAILS % job_id))
        else:
            self.job_tree_view = SGETreeView(os.popen(EMPTY_SGE_JOB_DETAILS))

        job_tab_vbox.addWidget(self.job_tree_view)
        self.job_tree_view.setAlternatingRowColors(1)
        self.job_tree_view.hide()

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
         
    def splashMessage(self, text):             
        self.splash.showMessage(text, Qt.AlignBottom)
        self.app.processEvents()
        






