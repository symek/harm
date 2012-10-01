from PyQt4.QtGui import QMenu, QIcon, QAction
import os
import utilities

##########################################################
# Base Class for Context Menues:                         #
##########################################################

class ContextMenuBase():
    def buildActionStrings(self, callbacks):
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

    def findIcons(self):
        icons = {}
        path = "/STUDIO/scripts/harm/icons"
        files = os.listdir(path)
        for file in files:
            if os.path.isfile(os.path.join(path, file)):
                p, f  = os.path.split(file)
                f, ext = os.path.splitext(f)
                icons[f] = os.path.join(path, file)
        return icons
            

    def bindActions(self, actions):
        ''' 'Actions' are tuples of (name, caption) from which we build items for
           QMenu with 'name's and assign actions with 'caption' to it.'''
        icons = self.findIcons()
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

class JobsContextMenu(ContextMenuBase, QMenu):
    def __init__(self, context, position):
        super(JobsContextMenu, self).__init__()
        self.setTearOffEnabled(1)
        self.view    = context.views['jobs_view']
        self.model   = context.models['jobs_model']
        self.bindActions(self.buildActionStrings(self))
        self.execute(position)

    def _getIds(self, view=None, model=None):
        indexes  = self.view.selectedIndexes()
        ids = []
        for index in indexes:
            job_id   = self.model.root[index.row()][0].text
            task_ids = utilities.expand_pattern(self.model.root[index.row()][8].text)
            for task in task_ids:
                ids.append("%s.%s" % (job_id, task))
        return(" ".join(ids))
        
    def callback_delete(self):
        result = os.popen('qdel %s' % self._getIds()).read()
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

class TasksContextMenu(ContextMenuBase, QMenu):
    def __init__(self, context, position):
        super(TasksContextMenu, self).__init__()
        self.view    = context.views['tasks_view']
        self.model   = context.models['tasks_model']
    
        self.bindActions(self.buildActionStrings(self))
        self.execute(position)

    def _getIds(self, view=None, model=None):
        indexes  = self.view.selectedIndexes()
        job_ids  = [self.model.root[x.row()][0].text for x in indexes]
        task_ids = [self.model.root[x.row()][8].text for x in indexes]
        task_ids = zip(job_ids, task_ids)
        task_ids = list(set([".".join(x) for x in task_ids]))
        return(" ".join(task_ids))
        
    def callback_delete(self):
        result = os.popen('qdel %s' % self._getIds()).read()
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


