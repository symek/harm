from PyQt4.QtGui import QMenu, QIcon, QAction
import os
import utilities

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
        path = "/STUDIO/scripts/harm/icons"
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
        self.bind_actions(self.build_action_strings(self))
        self.execute(position)

    def _getIds(self, view=None, model=None):
        indexes  = self.view.selectedIndexes()
        indexes =  [self.view.proxy_model.mapToSource(index) for index in indexes]
        ids = []
        # FIXME: We should operate here on proxy_model, not model?
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
        result = os.popen('qdel -f %s' % self._getIds()).read()
        print result
        #print self._getIds()

    def callback_hold(self):
        result = os.popen('qhold -h u %s' % self._getIds()).read()
        print result
        
    def callback_unhold(self):
        result = os.popen('qalter -h U %s' % self._getIds()).read()
        print result

    def callback_suspend(self):
        result = os.popen('qmod -sj %s' %  self._getIds()).read()
        print result

    def callback_unsuspend(self):
        result = os.popen('qmod -usj %s' %  self._getIds()).read()
        print result

    def callback_reschedule(self):
        result = os.popen('qmod -rj %s' %  self._getIds()).read()
        print result

    def callback_clear_error(self):
        result = os.popen('qmod -cj %s' %  self._getIds()).read()
        print result


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

    def _getIds(self, view=None, model=None):
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
        result = os.popen('qdel -f %s' % self._getIds()).read()
        #result = self._getIds()
        print result

    def callback_hold(self):
        result = os.popen('qhold -h u %s' % self._getIds()).read()
        print result
        
    def callback_unhold(self):
        result = os.popen('qalter -h U %s' % self._getIds()).read()
        print result

    def callback_suspend(self):
        result = os.popen('qmod -sj %s' %  self._getIds()).read()
        print result

    def callback_unsuspend(self):
        result = os.popen('qmod -usj %s' %  self._getIds()).read()
        print result

    def callback_reschedule(self):
        result = os.popen('qmod -rj %s' %  self._getIds()).read()
        print result

    def callback_clear_error(self):
        result = os.popen('qmod -cj %s' %  self._getIds()).read()
        print result

    def compare_experimental(self):
        # Get tasks:
        ids = self._getIds()
        ids = ids.split()
        # Make sure user selected only two frames:
        # TODO: make possible compare two sequences!
        if len(ids) < 2:
            return
        elif len(ids) > 2:
            ids = ids[:2]
        ids = [x.split(".") for x in ids]

        # Retrieve images from a model
        # TODO: We don't have currently to get to the task details other
        # than currently loaded in detail view.
        # We could use the same model though... 
        model = self.context.views['job_detail_view'].model
        if 'OUTPUT_PICTURE' in model._dict:
            p0 = model._dict['OUTPUT_PICTURE']
            p0 = utilities.padding(p0, 'shell')
            p1 = p0[0].replace("*", str(ids[0][1]).zfill(p0[2]))
            p2 = p0[0].replace("*", str(ids[1][1]).zfill(p0[2]))
            os.system("/opt/package/houdini_12.0.687/bin/mplay -e c %s %s" % (p1, p2))
            


