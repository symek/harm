from PyQt4.QtGui import QMenu, QIcon, QAction
import os
import utilities
import constants

# Placeholder for future plugable backend
import slurm as backend


##########################################################
# Base Class for Context Menues:                         #
##########################################################

class ContextMenuBase():
    def build_action_strings(self, callbacks):
        '''Creates a list of tuples consisting name and caption of the actions built
           from callbacks class methods.'''
        actions = []
        # 
        for item in callbacks:
            if item.startswith("callback_"):
                item = item.split("_")
                item = item[1:]
                action = {}
                action['name'] = "_".join(item)
                action['capition'] = " ".join([l.title() for l in item])
                actions.append(action)
            # Anything other than "callback_*" means separator.
            else:
                action = {}
                action['name'] = ""
                action['capition'] = ''
                actions.append(action)
        return actions

    def find_icons(self):
        icons = {}
        path  = self.context.config['HARM_ICON']
        files = os.listdir(path)
        for file in files:
            if os.path.isfile(os.path.join(path, file)):
                p, f  = os.path.split(file)
                f, ext = os.path.splitext(f)
                icons[f] = os.path.join(path, file)
        return icons
            

    def bind_actions(self, actions):
        ''' 'Actions' are tuples of (name, caption) from which we build items for
           QMenu with 'name's and assign actions with 'caption' to it.
        '''
        icons = self.find_icons()
        for action in actions:
            qtaction = self.addAction(action['capition'])
            if action['name'] in icons.keys():
                icon = QIcon(icons[action['name']])
                qtaction.setIcon(icon)
            qtaction.setIconVisibleInMenu(1)
            if action['name'] == "": 
                qtaction.setSeparator(True)
            self.__setattr__(action['name'], qtaction)

    def execute(self, position):
        action = self.exec_(position)
        if action:
            action = 'callback_' + "_".join([str(x).lower() for x in str(action.text()).split()])
            self.__getattribute__(action)()

    def get_selected_items(self, view=None, model=None, key='ARRAY_JOB_ID'):
        """ Returns a list of values curretly selected usign 'key' as column filter.
        """
        indices    = self.view.selectedIndexes()
        item_index = self.model.get_key_index(key)
        indices    = [self.view.proxy_model.mapToSource(index)  for index in indices]
        items      = [self.model._data[index.row()][item_index] for index in indices]
        return list(set(items))         

###########################################################
# Jobs view context menu:#
###########################################################

# 'callback_copy_to_nuke', 
#                           'callback_update_from_database',
#                           'callback_clear_error',

class JobsContextMenu(QMenu, ContextMenuBase):
    def __init__(self, context, position):
        super(self.__class__, self).__init__()
        self.view    = context.views['jobs_view']
        self.model   = context.models['jobs_model']
        self.app     = context.app
        self.context = context
        items = [x for x in dir(self) if x.startswith('callback_')]
        self.item_list = ['callback_hold',
                          'callback_unhold',
                          'callback_suspend',
                          'callback_resume',
                          'callback_reschedule',
                          "",
                          'callback_delete']

        self.bind_actions(self.build_action_strings(self.item_list))
        self.execute(position)


    def callback_hold(self):
        """ Calls hold command of bakend for a selected job's id.
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.hold_job(jobs)
        view  = self.context.views['job_detail_basic_view']
        view.setPlainText("\n".join(result))
        
    def callback_unhold(self):
        """ Calls unhold command of bakend for a selected job's id.
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.unhold_job(jobs)
        view  = self.context.views['job_detail_basic_view']
        view.setPlainText("\n".join(result))


    def callback_suspend(self):
        """ Suspend jobs.
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.suspend_job(jobs)
        view  = self.context.views['job_detail_basic_view']
        view.setPlainText("\n".join(result))

    def callback_resume(self):
        """ Resume jobs (unsuspend).
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.resume_job(jobs)
        view  = self.context.views['job_detail_basic_view']
        view.setPlainText("\n".join(result))

    def callback_reschedule(self):
        """ Reschedule jobs.
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.reschedule_job(jobs)
        view  = self.context.views['job_detail_basic_view']
        view.setPlainText("\n".join(result))

    def callback_delete(self):
        """ Cancel jobs.
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.cancel_job(jobs)
        view  = self.context.views['job_detail_basic_view']
        view.setPlainText("\n".join(result))

    def callback_clear_error(self):
        result = os.popen('qmod -cj %s' %  self.get_item_id()).read()
        print result

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

    def callback_update_from_database(self):
        """Update per task entires in database job entry with qacct -j job_id query.
        """
        from couchdb import Server
        from ordereddict import OrderedDict
        # FIXME  these should come from Config():
        db = 'sge_db' 
        server = Server(os.getenv("CDB_SERVER"))
        # Connect to database
        if db in server: db = server[db]
        else: db = server.create(db)
        # Deal with models' indices,
        # TODO: Is this the best place to get unique rows indices?
        indices  = self.view.selectedIndexes()
        indices  = [self.view.proxy_model.mapToSource(index) for index in indices]
        row_idxs = list(set([index.row() for index in indices]))
        job_id_index = self.model.get_key_index('JB_job_number')
        jobs = []
        # Loop per selected job:
        for row_idx in row_idxs:
            # Job id and its entry from qacct:
            job_id = self.model._data[row_idx][job_id_index]
            model  = utilities.read_qacct(job_id, 0)
            # Database doc and relevant sub-entry:
            job   = db[job_id]
            tasks = []
            #  Model task's detail the same way, they are in qstat -xml:
            for task in model:
                job_id, task_id = task.split(".")
                task_dir = {}
                task_dir['JAT_status'] = '65536'
                task_dir['JAT_scaled_usage_list'] = dict()
                task_dir['JAT_task_number'] = task_id
                task_dir['HARM_cdb_logged'] = True
                task_dir['JAT_scaled_usage_list']['scaled'] = []
                scaled = []
                for data in model[task].keys():
                    _d = OrderedDict()
                    _d['UA_name'] = data
                    _d['UA_value']= model[task][data]
                    scaled.append(_d)
                task_dir['JAT_scaled_usage_list']['scaled'] = scaled
                tasks.append(task_dir)
            # new tasks list added to a job and job added to a jobs list
            # to be updated in bulk:
            job["JB_ja_tasks"]['ulong_sublist'] = tasks
            jobs.append(job)

        # Save docs in database:
        db.update(jobs)
  


    def callback_resubmit(self):
        """Resubmit job to SGE by recreating job details from finished job settings.
        """
        indices = self.view.selectedIndexes()
        indices = [self.view.proxy_model.mapToSource(index) for index in indices]
        job_ids = list(set([index.row() for index in indices]))
        job_id_index = self.model.get_key_index('JB_job_number')
        clipboard    = self.app.clipboard()
        read  = [];
        model = self.context.views['job_detail_view'].model
        for index in indices:
            job_id  = self.model._data[index.row()][job_id_index]
            if job_id not in read: 
                model.update(constants.SGE_JOB_DETAILS % job_id)
                # Job submission details:
                script    = model.get_value('JB_script_file')
                queue     = model.get_value('QR_name')
                PN_path   = queue  = model.get_value('PN_path')
                job_name  = model.get_value('JB_job_name')
                check     = model.get_value('JB_checkpoint_name')
                CE_name     = model.get_value('CE_name')
                CE_level    = model.get_value('CE_level')
                consume     = model.get_value('CE_consumable')
                


                print script
                print queue
                print PN_path
                print job_name
                print check
                print CE_level
                print CE_name
                print consume

                read.append(job_id)



#####################################################################
# Tasks view context menu                                           #
#####################################################################

class TasksContextMenu(QMenu, ContextMenuBase):
    def __init__(self, context, position):
        super(self.__class__, self).__init__()
        self.view      = context.views['tasks_view']
        self.model     = context.models['tasks_model']
        self.item_list = ['callback_show_sequence', 
                          'callback_show_in_folder',
                          'callback_clear_error',
                          "",
                          'callback_hold',
                          'callback_suspend',
                          'callback_reschedule',
                          'callback_unhold',
                          'callback_unsuspend',
                          "",
                          'callback_delete']
        self.context = context
        self.bind_actions(self.build_action_strings(self.item_list))
        self.execute(position)

    def get_item_id(self, view=None, model=None):
        indexes = self.view.selectedIndexes()
        indexes =  [self.view.proxy_model.mapToSource(index) for index in indexes]
        job_id_index   = self.model.get_key_index('JB_job_number')
        task_ids_index = self.model.get_key_index('tasks')
        job_ids  = [self.model._data[x.row()][job_id_index]   for x in indexes]
        task_ids = [self.model._data[x.row()][task_ids_index] for x in indexes]
        task_ids = zip(job_ids, task_ids)
        task_ids = list(set([".".join(x) for x in task_ids]))
        return(" ".join(task_ids))
        
    def callback_delete(self):
        result = os.popen('qdel -f %s' % self.get_item_id()).read()
        #result = self.get_item_id()
        print result

    def callback_hold(self):
        result = os.popen('qhold -h u %s' % self.get_item_id()).read()
        print result
        
    def callback_unhold(self):
        result = os.popen('qalter -h U %s' % self.get_item_id()).read()
        print result

    def callback_suspend(self):
        result = os.popen('qmod -sj %s' %  self.get_item_id()).read()
        print result

    def callback_unsuspend(self):
        result = os.popen('qmod -usj %s' %  self.get_item_id()).read()
        print result

    def callback_reschedule(self):
        result = os.popen('qmod -rj %s' %  self.get_item_id()).read()
        print result

    def callback_clear_error(self):
        result = os.popen('qmod -cj %s' %  self.get_item_id()).read()
        print result

    def callback_show_sequence(self):
        # Get tasks:
        ids = self.get_item_id()
        ids = ids.split()[0]
        config  = self.context.config
        model   = self.context.views['job_detail_view'].model
        picture = model.get_value('OUTPUT_PICTURE')
        if picture:
            picture = utilities.padding(picture[0], 'shell')[0]
            viewer  = config.convert_platform_path(config['image_viewer'])
            os.system(viewer + " " + picture)

    def callback_show_in_folder(self):
        # Get tasks:
        ids = self.get_item_id()
        ids = ids.split()[0]
        config  = self.context.config
        model   = self.context.views['job_detail_view'].model
        picture = model.get_value('OUTPUT_PICTURE')
        if picture:
            folder, file  = os.path.split(picture[0])
            folder        = self.context.config.convert_platform_path(folder)
            file_manger   = config['file_manager']
            # FIXME: This is system specific
            os.system("%s %s" % (file_manger, folder))
