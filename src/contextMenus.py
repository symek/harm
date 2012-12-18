from PyQt4.QtGui import QMenu, QIcon, QAction
import os
import utilities
import constants
#from models import JobDetailModel

##########################################################
# Base Class for Context Menues:                         #
##########################################################

class ContextMenuBase():
    def build_action_strings(self, callbacks):
        '''Creates a list of tuples consisting name and caption of the actions built
           from callbacks class methods.'''
        actions = []
        for item in dir(self):
            if item.startswith('callback'):
                item = item.split("_")
                item = item[1:]
                action = {}
                action['name'] = "_".join(item)
                action['capition'] = " ".join([l.title() for l in item])
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
           QMenu with 'name's and assign actions with 'caption' to it.'''
        icons = self.find_icons()
        for action in actions:
            qtaction = self.addAction(action['capition'])
            if action['name'] in icons.keys():
                icon = QIcon(icons[action['name']])
                qtaction.setIcon(icon)            
            qtaction.setIconVisibleInMenu(1)
            self.__setattr__(action['name'], qtaction)

    def execute(self, position):
        action = self.exec_(position)
        if action:
            action = 'callback_' + "_".join([str(x).lower() for x in str(action.text()).split()])
            self.__getattribute__(action)()


###########################################################
# Jobs view context menu:#
###########################################################

class JobsContextMenu(QMenu, ContextMenuBase):
    def __init__(self, context, position):
        super(self.__class__, self).__init__()
        self.view    = context.views['jobs_view']
        self.model   = context.models['jobs_model']
        self.app     = context.app
        self.context = context
        self.bind_actions(self.build_action_strings(self))
        self.execute(position)

    def get_item_id(self, view=None, model=None):
        indexes = self.view.selectedIndexes()
        indexes = [self.view.proxy_model.mapToSource(index) for index in indexes]
        ids = []
        job_id_index   = self.model.get_key_index('JB_job_number')
        task_ids_index = self.model.get_key_index('tasks')
        for index in indexes:
            job_id         = self.model._data[index.row()][job_id_index]            
            task_ids       = self.model._data[index.row()][task_ids_index]
            task_ids       = utilities.expand_pattern(task_ids)
            for task in task_ids:
                ids.append("%s.%s" % (job_id, task))
        return(" ".join(ids))
        
    def callback_delete(self):
        result = os.popen('qdel -f %s' % self.get_item_id()).read()
        print result
        #print self.get_item_id()

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

    def callback_copy_to_nuke(self):
        '''Creates a Nuke's paste string to create ReadNodes from 
        selected render jobs.'''
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


#####################################################################
# Tasks view context menu                                           #
#####################################################################

class TasksContextMenu(QMenu, ContextMenuBase):
    def __init__(self, context, position):
        super(self.__class__, self).__init__()
        self.view    = context.views['tasks_view']
        self.model   = context.models['tasks_model']
        self.context = context
        self.bind_actions(self.build_action_strings(self))
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
