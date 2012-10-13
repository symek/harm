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
        self.connect(self.jobs_view, SIGNAL("clicked(const QModelIndex&)"),  
                     self.jobs_view_clicked)
        #self.connect(self.finished_view, SIGNAL("clicked(const QModelIndex&)"),  
        #             self.finished_view_clicked)
        #self.connect(self.tasks_view, SIGNAL("clicked(const QModelIndex&)"),  
        #             self.tasks_view_clicked)
        #self.connect(self.right_tab_widget, SIGNAL("currentChanged(const int&)"),  
        #             self.update_std_views)
        self.connect(self.refreshAction, SIGNAL('triggered()'), 
                     self.refreshAll)
        #self.connect(self.job_view_combo, SIGNAL('currentIndexChanged(int)'), 
        #             self.change_job_view)
        #self.connect(self.machine_view_combo, SIGNAL('currentIndexChanged(int)'), 
        #             self.change_machine_view)
        #self.connect(self.jobs_filter_line, SIGNAL('textChanged(const QString&)'),\
        #             self.set_jobs_proxy_model_wildcard)   
        #self.connect(self.tasks_onlySelected_toggle, SIGNAL('stateChanged(int)'),\
        #             self.set_tasks_proxy_model_filter)   
        #self.connect(self.job_details_filter_line, SIGNAL('textChanged(const QString&)'),\
        #             self.set_job_detail_proxy_model_wildcard)  

    def refreshAll(self):
        self.jobs_view.update_model(SGE_JOBS_LIST_GROUPED)
        self.tasks_view.update_model(SGE_JOBS_LIST, 'queue_info')
        self.machine_view.update_model(SGE_CLUSTER_LIST, 'qhost')
        self.jobs_view.resizeRowsToContents()
        self.tasks_view.resizeRowsToContents()
        self.machine_view.resizeRowsToContents()

    def jobs_view_clicked(self, index):
        '''Calls for selecting job on Jobs View.'''
        #model = self.jobs_view.proxy_model
        #print model.data(model.index(index.row(), 0)).toString()
        s_index = self.jobs_view.proxy_model.mapToSource(index)
        job_id_index = self.jobs_view.model.get_key_index("JB_job_number")
        job_id  = self.jobs_view.model._data[s_index.row()][job_id_index]
        if self.right_tab_widget.currentIndex() == 0:
            self.job_detail_view.update(job_id)
        #elif self.right_tab_widget.currentIndex() in (1, 2): pass
            #self.update_stat_view(job_id)   
        #self.update_job_model_from_jobs(indices)
        #self.set_tasks_proxy_model_filter(0)
        #job_id = self.jobs_model.root[indices.row()][0].text

        #
    
    def tasks_view_clicked(self, indices):
        '''Calls for selecting job on Task View.'''
        s_index = self.tasks_view.proxy_model.mapToSource(index)
        job_id_index = self.jobs_view.model.get_key_index("JB_job_number")
        job_id  = self.jobs_view.model._data[s_index.row()][job_id_index]

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