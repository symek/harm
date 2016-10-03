import os, time
import utilities
from constants import *
import tokens
import slurm
#PyQt4:
from PyQt4.QtCore  import *
from PyQt4.QtGui   import * 
from PyQt4         import QtGui




class HarmMainWindowCallbacks():
    '''Holds only callbacks on various Qt Sigmals inside a main window.'''

    def setupSLOTS(self):
        # Update Job View SIGNAL:
        self.connect(self.refreshAction, SIGNAL('triggered()'), 
                     self.refreshAll)
        # Updates tasks view to focus on selected job
        self.connect(self.jobs_view, SIGNAL("clicked(const QModelIndex&)"),  
                     self.jobs_view_clicked)
        # Udates job detail view and stderr, stdout tabs
        self.connect(self.tasks_view, SIGNAL("clicked(const QModelIndex&)"),  
                     self.tasks_view_clicked)
        # 
        self.connect(self.tasks_onlySelected_toggle, SIGNAL('stateChanged(int)'),\
                    self.set_tasks_view_filter) 
        #   
        self.connect(self.set_user_action, SIGNAL('triggered()'), 
                     self.set_user)
        # Updates job view based on filter provided by user
        self.connect(self.jobs_filter_line, SIGNAL('returnPressed(const QString&)'),\
                     self.set_jobs_view_filter)
        # Updates history query based on user provided username. 
        self.connect(self.history_user, SIGNAL('editingFinished()'),\
                     self.set_history_user)
        # ?
        self.connect(self.history_view, SIGNAL("clicked(const QModelIndex&)"),  
                    self.history_view_clicked)
        # Updates detail, stdout/err view for sepected task.
        self.connect(self.running_view, SIGNAL("clicked(const QModelIndex&)"),  
                     self.running_task_view_clicked)

        # self.connect(self.job_detail_filter_line, SIGNAL('textChanged(const QString&)'),\
        #              self.set_job_detail_view_filter)   
        # self.connect(self.tasks_view, SIGNAL("doubleClicked(const QModelIndex&)"),  
        #              self.tasks_view_doubleClicked)
        # self.connect(self.tasks_colorize_style, SIGNAL('currentIndexChanged(int)'),\
                     # self.set_tasks_colorize_style)
        # self.connect(self.job_stdout_search_line, SIGNAL('textChanged(const QString&)'),\
        #              self.set_jobs_stdout_view_search) 
        # self.connect(self.job_view_combo, SIGNAL('currentIndexChanged(int)'), 
        #              self.change_job_view)
        #self.connect(self.finished_view, SIGNAL("clicked(const QModelIndex&)"),  
        #self.connect(self.right_tab_widget, SIGNAL("currentChanged(const int&)"),  
        #             self.update_std_views)
        #self.connect(self.machine_view_combo, SIGNAL('currentIndexChanged(int)'), 
        #             self.change_machine_view)
        #             self.finished_view_clicked)
        #self.connect(self.job_details_filter_line, SIGNAL('textChanged(const QString&)'),\
        #             self.set_job_detail_proxy_model_wildcard)  

    def refreshAll(self):
        '''Refreshes jobs/tasks/machine views. Automatically called by self.timer too. '''
        self.jobs_view.update_model(50)
        self.tasks_view.update_model(SLURM_JOBS_LIST, 'queue_info')
        self.running_view.update_model(SLURM_RUNNING_JOBS_LIST, 'queue_info')
        self.machine_view.update_model()
        self.jobs_view.resizeRowsToContents()
        self.tasks_view.resizeRowsToContents()
        # self.machine_view.resizeRowsToContents()

    def autoRefresh(self):
        if self.auto_refresh_toggle.isChecked():
            self.refreshAll()

    def set_user(self):
        user = utilities.get_username()
        self.jobs_filter_line.setText("USER:%s" % user)
        #self.set_jobs_view_filter()

    def jobs_view_clicked(self, index):
        '''Calls for selecting job on Jobs View.
        '''
        # First we map selected proxy index to the real one.
        s_index      = self.jobs_view.proxy_model.mapToSource(index)
        # then we look for our indices of fields in model header.
        job_id_index = self.jobs_view.model.get_key_index("JOBID")
        state_index  = self.jobs_view.model.get_key_index("STATE")
        # with that, we retrieve informations:
        job_id       = self.jobs_view.model._data[s_index.row()][job_id_index]
        state        = self.jobs_view.model._data[s_index.row()][state_index]
        #
        self.tasks_view.update_model(job_id)
        self.set_tasks_view_filter(job_id)

        self.job_detail_basic_view_update(job_id)

        # Update job detail view in case its tab is visible:
        # if self.right_tab_widget.currentIndex() == 0:
        #     self.job_detail_view.update_model(job_id)
        #     self.job_detail_basic_view_update(job_id)
        #     # Tree view active:
        #     if self.job_view_combo.currentIndex() == 2:
        #         self.job_detail_tree_view.update_model(job_id)

        # We set task view filter to currently selected AND runnig jobs,
        # or update tasks view with past jobs using database:
        # if state != 'cdb': 
        # else:
            # updat_db() calls update_job_details_db() first to read database
            # then parses query to look for per frame info and updats tasksModel._dict
            # with that data.
            # self.tasks_view.update_model_db(job_id)
            # self.set_tasks_view_filter(None)
    
    def tasks_view_clicked(self, index):
        '''Calls for selecting job on Task View.
        '''
        s_index       = self.tasks_view.proxy_model.mapToSource(index)
        job_id_index  = self.tasks_view.model.get_key_index("JOBID")
        job_id        = self.tasks_view.model._data[s_index.row()][job_id_index]
        task_id_index = self.tasks_view.model.get_key_index('ARRAY_TASK_ID')
        task_id       = self.tasks_view.model._data[s_index.row()][task_id_index]

        # That needs to be done for others widgets relaying on job_detail_view
        # Update job detail only if it's not already up to date already:
        update_details_flag = True

        if update_details_flag:
                self.job_detail_view.update_model(job_id, task_id)
        
        # Update both std out/err widgets:
        tab_index = self.right_tab_widget.currentIndex() 
        if tab_index in (1,2):
            self.update_std_views(job_id, task_id, tab_index)


    def running_task_view_clicked(self, index):
        '''Calls for selecting job on Task View.
        '''
        s_index       = self.running_view.proxy_model.mapToSource(index)
        job_id_index  = self.running_view.model.get_key_index("JOBID")
        job_id        = self.running_view.model._data[s_index.row()][job_id_index]
        task_id_index = self.running_view.model.get_key_index('ARRAY_TASK_ID')
        task_id       = self.running_view.model._data[s_index.row()][task_id_index]

        # That needs to be done for others widgets relaying on job_detail_view
        # Update job detail only if it's not already up to date already:
        update_details_flag = True

        if update_details_flag:
                self.job_detail_view.update_model(job_id, task_id)
        
        # Update both std out/err widgets:
        tab_index = self.right_tab_widget.currentIndex() 
        if tab_index in (1,2):
            self.update_std_views(job_id, task_id, tab_index)

      

    def tasks_view_doubleClicked(self, index):
        '''Double clicking on task calls image viewer (mplay for now)
        TODO: place for Config() class.
        '''
        s_index       = self.tasks_view.proxy_model.mapToSource(index)
        job_id_index  = self.tasks_view.model.get_key_index("JB_job_number")
        task_id_index = self.tasks_view.model.get_key_index("tasks")
        job_id        = self.tasks_view.model._data[s_index.row()][job_id_index]
        task_id       = self.tasks_view.model._data[s_index.row()][task_id_index]

        # Update job detail only if it's not already updated:
        if self.job_detail_view.model._dict['JB_job_number'] != job_id:
           self.job_detail_view.update_model(job_id)

        # Get image info, it might not be there though:            
        picture = self.job_detail_view.model.get_value("OUTPUT_PICTURE")
        if picture:
            # We want a single specific frame, not a whole sequence,
            # this is what padding(filename, None, frame) is doing:
            picture = utilities.padding(picture[0], None, task_id)
            # Note: convert_* is inside config as it allows us to customize
            # platform specific prefixes in coherent way, otherwise it should
            # be probably placed in utilities module: 
            viewer  = self.config.convert_platform_path(self.config['image_viewer'])
            os.system(viewer + " " + picture[0])
        else:
            print "No output-image information found."


    def update_std_views(self, job_id, task_id, tab_index):
        '''Read from disk files logs specified by selected tasks..
        '''         
        data     = self.job_detail_view.model
        if not 'StdOut' in data._dict.keys() or \
        not 'StdErr' in data._dict.keys():
            return 

        stdout_file = data._dict['StdOut']
        stderr_file = data._dict['StdErr']
        
        # Stdout Tab:
        if tab_index == 1:
            stdout_file = self.config.convert_platform_path(stdout_file) 
            try:
                stdout_file  = open(stdout_file, 'r')
                self.stdout_view.setPlainText(stdout_file.read())
                self.stdout_view.moveCursor(QtGui.QTextCursor.End)
                self.stdout_view.ensureCursorVisible()
                stdout_file.close()
            except: 
                self.stdout_view.setPlainText("Couldn't open %s" % stdout_file)

        # Stderr Tab:
        elif tab_index == 2:
            stderr_file = self.config.convert_platform_path(stderr_file)
            try: 
                stderr_file  = open(stderr_file, 'r')
                self.stderr_view.setPlainText(stderr_file.read())
                self.stderr_view.moveCursor(QtGui.QTextCursor.End)
                self.stderr_view.ensureCursorVisible()
                stderr_file.close()
            except: 
                self.stderr_view.setPlainText("Couldn't open %s" % stderr_file)


    def set_jobs_view_filter(self, wildcard):
        '''Sets a filter for jobs view according to user input in jobs_filter_line.
        Basic syntax is header_name:value, where header_name might either alias used
        in GUI, or real name used in model. We should provide the latter one with popup
        or something.'''
        from fnmatch import fnmatch
        # By default we filter users: 
        column_name   =  None
        wildcard      = str(wildcard)
        # basic syntax for specifying headers:

        wildcard    = wildcard.split(":")
        if len(wildcard) > 1:
            column_name = wildcard[0]
            wildcard  = wildcard[1]
        else:
            wildcard = wildcard[0]

        # Find real variable name from header name:
        if column_name in tokens.header.values():
            real_name = tokens.header.keys()[tokens.header.values().index(column_name)]
            # If token matches real name or alias name assign new column:
            if fnmatch(column_name, real_name) or fnmatch(column_name, tokens.header[real_name]):
                column_name = real_name

        elif not column_name:
            column_index =-1
        else:
            column_index = self.jobs_view.model.get_key_index(column_name)
            
        # Finally our job:
        self.jobs_view.proxy_model.setFilterKeyColumn(column_index)
        self.jobs_view.proxy_model.setFilterWildcard(wildcard)
        self.jobs_view.resizeRowsToContents()

    def set_tasks_view_filter(self, job_id):
        '''Sets a filter according to job selection in jobs view.'''
        # Early exit on non-ids:
        if job_id == None: 
            self.tasks_view.proxy_model.setFilterWildcard("")
            self.tasks_view.resizeRowsToContents()
            self.tasks_view.resizeColumnsToContents()
            return

        # Proceed with setting filter on job number column:
        job_id_index  = self.tasks_view.model.get_key_index("JB_job_number")
        # Our column might not exist:
        if job_id_index:
            self.tasks_view.proxy_model.setFilterKeyColumn(job_id_index)
            if self.tasks_onlySelected_toggle.isChecked():
                self.tasks_view.proxy_model.setFilterWildcard(str(job_id))
            else:
                self.tasks_view.proxy_model.setFilterWildcard("")

        # Usual clean up:
        self.tasks_view.resizeRowsToContents()
        self.tasks_view.resizeColumnsToContents()

    def set_history_user(self):
        user = self.history_user.text()
        self.history_view.update_model(user)


    def history_view_clicked(self, index):
        job_id_index  = self.history_view.model.get_key_index("JobID")
        job_id        = self.history_view.model._data[index.row()][job_id_index]

        import slurm
        data, header = slurm.get_accounted_job_details(job_id)
        self.job_detail_view.model.reset()
        self.job_detail_view.model.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.job_detail_view.model._data = data
        self.job_detail_view.model._head = header
        self.job_detail_view.model.emit(SIGNAL("layoutChanged()"))
        
        self.resizeRowsToContents()
        self.resizeColumnsToContents()


    def job_detail_basic_view_update(self, job_id):
        '''Updates texted in detail basic view.
        It's a text viewer sutable for very simple
        presentation of data'''
        #TODO: This is workaround for a lack of html widget.
        # text = utilities.render_basic_job_info(self.job_detail_view.model._dict)
        # text += utilities.render_basic_task_info(self.job_detail_view.model._tasks)
        # FIXME: read_rtime() is very slow:
        #text += utilities.read_rtime(job_id)
        text   = slurm.render_job_stats_to_text(job_id)
        self.job_detail_basic_view.setPlainText(str(text))

    def set_job_detail_view_filter(self, text):
        '''Filters job details view.'''
        key = str(self.job_detail_filter_line.text())
        self.job_detail_view.proxy_model.setFilterWildcard(key)
        self.job_detail_view.resizeRowsToContents()
        self.job_detail_view.resizeColumnsToContents()

    def set_tasks_colorize_style(self, style):
        """Sets color style for TasksView deletgate.
        """
        # For now just that:
        self.tasks_view.delagate.colorize_style = style

    def set_jobs_stdout_view_search(self, pattern):
        """ Triggers search of a given pattern in stdout
        """
        #pattern = self.job_stdout_search_line.text()
        if self.stdout_view.find(pattern):
            self.stdout_view.ensureCursorVisible()

    def change_job_view(self, view):
        '''Switch job view between table and tree views.'''
        if view == 0:
            self.job_detail_tree_view.hide()
            self.job_detail_view.show()     
        else:
            self.job_detail_view.hide()
            self.job_detail_tree_view.show()
        


    #####################################################################
    ### Old stuff



    def change_machine_view(self, view):
        '''Switch machines view between table and tree views.'''
        if view == 0:
            self.machine_tree_view.hide()
            self.machine_view.show()     
        else:
            self.machine_view.hide()
            self.machine_tree_view.show()
        

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

    """def finished_view_clicked(self, indices):
        '''Calls for selecting job on Task View.'''
        tm = {}
        for index in range(len(self.finished_model.root[0])):
            tm[self.finished_model.root[0][index].tag] = index
        job_id = self.finished_model.root[indices.row()][tm['jobnumber']].text
        self.update_stat_view(job_id)"""
           

    """def update_job_model_from_jobs(self, indices):
        '''Update job detialed view on selection in Jobs view.'''
        job_id  = self.jobs_model.root[indices.row()][0].text
        command = SGE_JOB_DETAILS % job_id
        self.job_model.update(os.popen(command))
        self.job_view.reset()"""

    """def update_job_model_from_tasks(self, indices):
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
            #self.job_tree_view.populate(self.job_tree_view.root)"""

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

    '''def set_job_detail_proxy_model_wildcard(self, wildcard):
        wildcard = wildcard.split(":")
        self.job_detail_proxy_model.setFilterWildcard(wildcard[-1])
        self.job_detail_tree_view.resizeRowsToContents() '''
