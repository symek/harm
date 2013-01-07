#PyQt:
from PyQt4.QtCore  import *
from PyQt4.QtGui   import *

#Harm:
from SGEModels import *
from constants import *
from contextMenus import *
import delegates
import models
import config

#System:
import os

###########################################################
# ViewConfig applies settings taken from a file or module #
###########################################################

class ViewConfig():
    '''This is only placeholder for future Config class.'''
    def configure(self):
        # Prototype of config class.
        conf = config.Config()
        # conf.load("/STUDIO/scripts/harm-sge/src/harm.conf")
        # if self.__class__.__name__ in conf.keys():
        #     c = conf[self.__class__.__name__]
        #     for item in c:
        #         self.__getattribute__(item[0])(item[1][0])
            
    def save_configure(self):
        pass


###########################################################
#       Base class for Views  (possibly to be removed     #
###########################################################

class ViewBase():
    '''Base Class for custom View objects. Perhpas should be replaced by
    more general concept (common for all harm objects). Main purpose of this class
    is to read/write configurations.'''
    order_columns = []
    hidden_columns = []
    def configure(self):
        '''Sets minimal configuration settings, then
        reads rest of the settings form config object.'''
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openContextMenu)
        self.setSortingEnabled(True)
        self.setCornerButtonEnabled(True)
        self.setSelectionBehavior(1)
        self.setAlternatingRowColors(1)
        self.setDragDropMode(4)
        self.horizontalHeader().setMovable(True)
        
    def update_model(self, *arg):
        '''This method is called by callback whenever model should be updated with
        data from database or qstat. It also hides and orders columns in models after that.'''
        self.proxy_model.reset()
        self.model.reset()
        self.model.update(*arg)

        # Clean up stuff after refresh: 
        self.set_column_order(self.order_columns)
        self.set_column_hidden(self.hidden_columns)

    def set_column_order(self, ordered_items):
        '''Reorder columns in provided order.'''
        # TODO: With setMovable() ordering doesn't work?
        #self.horizontalHeader().setMovable(True)?
        for column in range(len(ordered_items)):
            if ordered_items[column] in self.model._head.values():
                # We mind visual_index which changes on every loop's step, 
                # so this have to be rediscaverd again:
                column_index = self.model.get_key_index(ordered_items[column])
                visual_index = self.horizontalHeader().visualIndex(column_index)
                self.horizontalHeader().moveSection(visual_index, column)

    def set_column_hidden(self, hidden_columns):
        '''Hides column according to a provided list.'''
        for column in hidden_columns:
            if column in self.model._head.values():
                self.setColumnHidden(self.model.get_key_index(column), True)  


###############################################################
#           Jobs Table View (after testing I decided          #
#           to construct more specific views/models and less  #
#           rely on absract types.                            # 
###############################################################

class JobsView(QTableView, ViewBase):
    '''Keeps joined list of currently happening jobs, plus a history
    retrieved from a database. Basic actions via context menus and callbacks
    to tasks views and detail views.'''
    def __init__(self, context):
        '''We're: adding self to a global context class, binding context menues, 
           creating models (main and proxy), seting deletegs,  initializing config(),
           resizing columns/rows.'''
        super(self.__class__, self).__init__()
        # those are mandatory.
        self.context = context
        self.context.views['jobs_view'] = self
        self.configure()
        # Models:
        self.model = models.JobsModel(self)
        self.model.update(SGE_JOBS_LIST_GROUPED)
        # FIXME: history should be appended in update()...
        self.model.append_jobs_history()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setDynamicSortFilter(True)
        self.context.models['jobs_model'] = self.model
        self.context.models['jobs_proxy_model'] = self.proxy_model
        self.setModel(self.proxy_model)
        
        # Delegate:
        self.delagate = delegates.JobsDelegate(self.context)
        self.setItemDelegate(self.delagate)

        # Hiding/ordering:
        self.order_columns = 'JB_job_number JB_owner state tasks JB_name JAT_prio JB_submission_time queue_name'.split()
        self.set_column_order(self.order_columns)
        self.hidden_columns = ("slots", "queue_name")
        self.set_column_hidden(self.hidden_columns)

        # Clean:
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def openContextMenu(self, position):
        '''Context menu entry.'''
        self.context_menu = JobsContextMenu(self.context, self.mapToGlobal(position))

    # TODO: This is temporary to allow append_history to jobs view after refresh:
    def update_model(self, *arg):
        '''Overwrites update_model() to allow append history jobs to a model.'''
        self.model.reset()
        self.model.update(*arg)
        self.model.append_jobs_history()  
        self.set_column_order(self.order_columns)
        self.set_column_hidden(self.hidden_columns)



###############################################################
#     Task Table View                                         #
###############################################################

class TasksView(QTableView, ViewBase):
    def __init__(self, context):
        super(self.__class__, self).__init__()
        self.context = context
        self.context.views['tasks_view'] = self
        self.setEditTriggers(self.NoEditTriggers)
        self.configure()

        # Models:
        self.model = models.TaskModel(self)
        self.model.update(SGE_JOBS_LIST, 'queue_info', reverse_order=False)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setDynamicSortFilter(True)
        self.context.models['tasks_model'] = self.model
        self.context.models['tasks_proxy_model'] = self.proxy_model
        self.setModel(self.proxy_model)

        # Order/hidden:
        self.order_columns = 'JB_job_number tasks JB_owner JAT_start_time queue_name JB_name'.split()
        self.set_column_order(self.order_columns)
        self.hidden_columns = "slots owner group project qname jobname department jobnumber \
                                account arid priority granted_pe".split()
        self.set_column_hidden(self.hidden_columns)

        # Clean:
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def openContextMenu(self, position):
        self.context_menu = TasksContextMenu(self.context, self.mapToGlobal(position))

    #FIXME: this probably shouldn't exists. 
    def update_model_db(self, job_id):
        from time import time
        t = time()
        self.model.reset()
        if DEBUG:
            print "TasksView.update_model_db (self.model.reset): %s" % str(time() - t)
        self.model.update_db(job_id)
        t = time()
        self.set_column_order(self.order_columns)
        self.set_column_hidden(self.hidden_columns)
        # Clean:
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        if DEBUG:
            print "TasksView.update_model_db: " + str(time() - t)



####################################################################
#  History Table view. There is a lot of tweaking of data here,    #
#  To make this really usable. First of all, these items should be #
#  displayed along with current Job, but SGE doesn't work this way #
####################################################################

class HistoryView(QTableView, ViewBase):
    def __init__(self, context):
        super(self.__class__, self).__init__()
        self.context = context
        self.configure()

        # Models:
        self.model = models.JobsHistoryModel(self)
        self.model.update(SGE_HISTORY_LIST)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setDynamicSortFilter(True)
        self.context.models['history_model'] = self.model
        self.context.models['history_proxy_model'] = self.proxy_model
        self.setModel(self.proxy_model)

        # Reorder columns in bellow order:        
        # FIXME: Move both bellow constants into Config class...
        self.order_columns = 'jobnumber taskid owner qsub_time start_time end_time \
                        jobname cpu maxvmem exit_status failed'.split()
        self.set_column_order(self.order_columns)

        # Hide columns:
        self.hidden_columns = 'ru_nvcsw group ru_isrss ru_nsignals arid priority ru_maxrss ru_nswap ru_majflt\
        ru_nivcsw granted_pe ru_msgsnd account ru_ixrss ru_ismrss ru_idrss ru_msgrcv ru_inblock ru_minflt\
        ru_oublock iow slots'.split()
        self.set_column_hidden(self.hidden_columns)

        # Clean:
        self.resizeColumnsToContents()
        self.resizeRowsToContents()




##########################################################################
#  Alternative Tree view for history. This class makes use of dictionary #
#  rotating, which allows it to build tree by arbitrary key.             #
##########################################################################

class JobsTreeHistoryView(QTreeWidget, ViewBase):
    def __init__(self, context):
        super(self.__class__, self).__init__()
        self.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.order_columns = 'jobnumber taskid owner qsub_time start_time \
        end_time jobname cpu maxvmem exit_status failed'.split()
        self.context = context
        self.configure()
        self._dict={}
        self.update(SGE_HISTORY_LIST, "owner")
        
        
    def update(self, sge_command, rotate_by_field=None):
        self._dict = models.qccet_to_dict(os.popen(sge_command).read(), True, self.order_columns)
        
        # FIXME: _dict once holds a list of dictonaries (when rotate_* is performed),
        # and sometimes a list of dictionaries, when no rotating is applied. 
        # This brings a mess into a table...
        if rotate_by_field:
            self._dict = models.rotate_nested_dict(self._dict, rotate_by_field)
            tmp =  models.SgeTableModelBase()
            self._head = models.SgeTableModelBase._tag2idx(tmp, self._dict[self._dict.keys()[0]][0])
        else:
            self._head = models.SgeTableModelBase._tag2idx(tmp, self._dict[[0]])

        self.clear()
        self.context.splashMessage("After clear")
        self.populate(self._dict)
        self.context.splashMessage("After populate")
        self.setHeaderLabels(self._head.values())
        self.context.splashMessage("After setHeaderLabels")

         # Hide columns:
        hidden_columns = 'ru_nvcsw group ru_isrss ru_nsignals arid priority ru_maxrss ru_nswap ru_majflt\
        ru_nivcsw granted_pe ru_msgsnd account ru_ixrss ru_ismrss ru_idrss ru_msgrcv ru_inblock ru_minflt\
        ru_oublock iow slots'.split()
        for column in hidden_columns:
            if column in self._head.values():                
                key_index = [k for k, v in self._head.iteritems() if v == column][0]
                self.setColumnHidden(key_index, True)
        self.context.splashMessage("After setColumnHidden")

        # TODO: Reorder columns! (probably by reordering dictionaries).
        self.context.splashMessage("After update")

    def columnCount(self, parent):
       return len(self._head)


    def populate(self, data, parent=None):
        if not parent:
            parent = self
        for row in data:
            self.context.splashMessage("Populating %s" % str(row))
            rowItem = QtGui.QTreeWidgetItem(parent)
            rowItem.setText(0, str(row))
            rowItem.setExpanded(True)
            if isinstance(data[row], dict):
                leafs = [data[row]]
            elif isinstance(data[row], list):
                leafs = data[row]  
            for child in leafs:
                childItem = QtGui.QTreeWidgetItem(rowItem)
                for key in range(len(child.keys())):
                #    if child.keys()[key] in self.order_columns:
                #        key = self.order_columns.index(child.keys()[key])                   
                    childItem.setText(key, str(child[child.keys()[key]]))
                    childItem.setExpanded(True)



###############################################################
#     Machine Table View                                      #
###############################################################

class MachineView(QTableView, ViewBase):
    def __init__(self, context):
        super(self.__class__, self).__init__()
        self.context = context
        self.context.views['machine_view'] = self
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openContextMenu)
        self.configure()

        # Models:
        self.model = models.MachineModel()
        self.model.update(SGE_CLUSTER_LIST, 'qhost')
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setDynamicSortFilter(True)
        self.context.models['machine_model'] = self.model
        self.context.models['machine_proxy_model'] = self.proxy_model
        self.setModel(self.proxy_model)

        # Clean:
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

         # Delegate:
        self.delagate = delegates.MachinesDelegate(self.context)
        self.setItemDelegate(self.delagate)

    def openContextMenu(self, position): pass
        #self.context_menu = TasksContextMenu(self.context, self.mapToGlobal(position))



###############################################################
#     Job Detail Table View                                      #
###############################################################

class JobDetailView(QTableView, ViewBase):
    def __init__(self, context):
        super(self.__class__, self).__init__()
        self.context = context
        self.context.views['job_detail_view'] = self
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openContextMenu)
        self.configure()

        # Models:
        self.model = models.JobDetailModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setDynamicSortFilter(True)
        self.proxy_model.setFilterCaseSensitivity(0)
        self.context.models['job_detail_model'] = self.model
        self.context.models['job_detail_proxy_model'] = self.proxy_model
        self.setModel(self.proxy_model)

        # Clean:
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.horizontalHeader().setResizeMode(3)

    def openContextMenu(self, position): pass
        #self.context_menu = TasksContextMenu(self.context, self.mapToGlobal(position))


    def update_model(self, jobid):
        self.model.reset()
        self.model.update(SGE_JOB_DETAILS % jobid, 'djob_info')
        self.resizeRowsToContents()
        self.resizeColumnsToContents()
