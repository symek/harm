import os, time
import utilities
from constants import *
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
        self.connect(self.jobs_view, SIGNAL("clicked(const QModelIndex&)"),  
                     self.jobs_view_clicked)
        self.connect(self.tasks_view, SIGNAL("clicked(const QModelIndex&)"),  
                     self.tasks_view_clicked)
        self.connect(self.tasks_onlySelected_toggle, SIGNAL('stateChanged(int)'),\
                    self.set_tasks_view_filter)   
        self.connect(self.set_user_action, SIGNAL('triggered()'), 
                     self.set_user)
        self.connect(self.jobs_filter_line, SIGNAL('textChanged(const QString&)'),\
                     self.set_jobs_view_filter) 
        self.connect(self.job_detail_filter_line, SIGNAL('textChanged(const QString&)'),\
                     self.set_job_detail_view_filter)   
        self.connect(self.tasks_view, SIGNAL("doubleClicked(const QModelIndex&)"),  
                     self.tasks_view_doubleClicked)
        #self.connect(self.finished_view, SIGNAL("clicked(const QModelIndex&)"),  
        #self.connect(self.right_tab_widget, SIGNAL("currentChanged(const int&)"),  
        #             self.update_std_views)
        #self.connect(self.job_view_combo, SIGNAL('currentIndexChanged(int)'), 
        #             self.change_job_view)
        #self.connect(self.machine_view_combo, SIGNAL('currentIndexChanged(int)'), 
        #             self.change_machine_view)
        #             self.finished_view_clicked)
        #self.connect(self.job_details_filter_line, SIGNAL('textChanged(const QString&)'),\
        #             self.set_job_detail_proxy_model_wildcard)  

    def refreshAll(self):
        if time.time() - self.tick < 5:
            time.sleep(3)           
        self.jobs_view.update_model(SGE_JOBS_LIST_GROUPED)
        self.tasks_view.update_model(SGE_JOBS_LIST, 'queue_info')
        self.machine_view.update_model(SGE_CLUSTER_LIST, 'qhost')
        self.tick_tack()
        self.jobs_view.resizeRowsToContents()
        self.tasks_view.resizeRowsToContents()
        self.machine_view.resizeRowsToContents()

    def set_user(self):
        user = utilities.get_username()
        self.jobs_filter_line.setText("owner:%s" % user)
        #self.set_jobs_view_filter()

    def jobs_view_clicked(self, index):
        '''Calls for selecting job on Jobs View.'''
        s_index = self.jobs_view.proxy_model.mapToSource(index)
        job_id_index = self.jobs_view.model.get_key_index("JB_job_number")
        job_id  = self.jobs_view.model._data[s_index.row()][job_id_index]
        # Update job detail view in case it's visible
        # TODO: Perhaps this should be always performed?
        # Or only id we didn't 'cached' some how job?
        if self.right_tab_widget.currentIndex() == 0:
            self.job_detail_view.update_model(job_id)
            self.job_detail_basic_view_update()
        # Call this in case toggle onle_Selected is checked:
        self.set_tasks_view_filter(job_id)
        #elif self.right_tab_widget.currentIndex() in (1, 2): pass
            #self.update_stat_view(job_id)   
        #job_id = self.jobs_model.root[indices.row()][0].text
    
    def tasks_view_clicked(self, index):
        '''Calls for selecting job on Task View.'''
        s_index = self.tasks_view.proxy_model.mapToSource(index)
        job_id_index  = self.tasks_view.model.get_key_index("JB_job_number")
        job_id        = self.tasks_view.model._data[s_index.row()][job_id_index]

        # That needs to be done for others widgets relaying on job_detail_view
        # Update job detail only if it's not already updated:
        #if self.job_detail_view.model._dict['JB_job_number'] != job_id:
        self.job_detail_view.update_model(job_id)
        self.job_detail_basic_view_update()
        
        # Update both std out/err widgets:
        tab_index = self.right_tab_widget.currentIndex() 
        if tab_index in (1,2):
            task_id_index = self.tasks_view.model.get_key_index('tasks')
            task_id       = self.tasks_view.model._data[s_index.row()][task_id_index]
            self.update_std_views(job_id, task_id, tab_index)

        #self.update_job_model_from_tasks(indices)
        #job_id = self.tasks_model.root[indices.row()][0].text
        #self.update_stat_view(job_id)
        #self.update_image_view(job_id)

    def tasks_view_doubleClicked(self, index):
        """Double clicking on task calls image viewer (mplay for now)
        TODO: place for Config() class."""
        s_index       = self.tasks_view.proxy_model.mapToSource(index)
        job_id_index  = self.tasks_view.model.get_key_index("JB_job_number")
        job_id        = self.tasks_view.model._data[s_index.row()][job_id_index]

        # Update job detail only if it's not already updated:
        if self.job_detail_view.model._dict['JB_job_number'] != job_id:
            self.job_detail_view.update_model(job_id)

        # Get image info:            
        if 'OUTPUT_PICTURE' in self.job_detail_view.model._dict:
            picture = self.job_detail_view.model._dict['OUTPUT_PICTURE']
            picture = utilities.padding(picture, 'shell')
            os.system("/opt/package/houdini_12.0.687/bin/mplay %s" % picture[0])
        else:
            print "No image."


    def update_std_views(self, job_id, task_id, tab_index):
        '''Read from disk logs specified by selected tasks..'''
        PN_path  = None
        job_name = None            
        data = self.job_detail_view.model._dict
        if "PN_path" in data: PN_path = data['PN_path']    
        if "JB_job_name" in data: job_name = data['JB_job_name']

        # Stdout Tab:
        if PN_path and job_name and tab_index == 1:
            PN_path = "%s%s.o%s.%s" % (PN_path, job_name, job_id, task_id)
            try:
                stdout_file  = open(PN_path, 'r')
                self.stdout_view.setPlainText(stdout_file.read())
                stdout_file.close()
            except: 
                self.stdout_view.setPlainText("Can't find %s" % PN_path)

        # Stderr Tab:
        elif PN_path and job_name and tab_index == 2:
            PN_path = "%s%s.e%s.%s" % (PN_path, job_name, job_id, task_id)
            try: 
                stderr_file  = open(PN_path, 'r')
                self.stderr_view.setPlainText(stderr_file.read())
                stderr_file.close()
            except: 
                self.stderr_view.setPlainText("Can't find %s" % PN_path)


    def set_jobs_view_filter(self, wildcard):
        '''Sets a filter for jobs view according to user input in jobs_filter_line'''
        wildcard = wildcard.split(":")
        self.jobs_view.proxy_model.setFilterWildcard(wildcard[-1])
        self.jobs_view.resizeRowsToContents()
        # if len(wildcard) > 1:
        #     for x in range(len(self.jobs_model.root[0])):
        #         tag = str(self.jobs_model.root[0][x].tag)
        #         if tag in tokens.header.keys():
        #             column_name = tokens.header[tag]
        #             if str(wildcard[0]).lower() == column_name.lower():
        #                 self.jobs_view.proxy_model.setFilterKeyColumn(x)
        #                 break


    def set_tasks_view_filter(self, job_id):
        '''Sets a filter according to job selection in jobs view.'''
        job_id_index  = self.tasks_view.model.get_key_index("JB_job_number")
        self.tasks_view.proxy_model.setFilterKeyColumn(job_id_index)
        if self.tasks_onlySelected_toggle.isChecked():
            self.tasks_view.proxy_model.setFilterWildcard(str(job_id))
        else:
            self.tasks_view.proxy_model.setFilterWildcard("")
        self.tasks_view.resizeRowsToContents()
        self.tasks_view.resizeColumnsToContents()

    def job_detail_basic_view_update(self):
        '''Updates texted in detail basic view.
        It's a text viewer sutable for very simple
        presentation of data'''
        text = utilities.render_basic_job_info(self.job_detail_view.model._dict)
        text += utilities.render_basic_task_info(self.job_detail_view.model._tasks)
        self.job_detail_basic_view.setPlainText(str(text))

    def set_job_detail_view_filter(self, text):
        '''Filters job details view.'''
        key = str(self.job_detail_filter_line.text())
        self.job_detail_view.proxy_model.setFilterWildcard(key)
        self.job_detail_view.resizeRowsToContents()
        self.job_detail_view.resizeColumnsToContents()


    #####################################################################
    ### Old stuff


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
