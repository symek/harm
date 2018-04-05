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
                          "",
                          'callback_reschedule',
                          "",
                          'callback_edit',
                          "",
                          'callback_show_sequence',
                          "",
                          'callback_cancel',]

        self.bind_actions(self.build_action_strings(self.item_list))
        self.execute(position)


    def callback_hold(self):
        """ Calls hold command of bakend for a selected job's id.
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.hold_job(jobs)
        self.context.GUI.message("\n".join(result))

    def callback_unhold(self):
        """ Calls unhold command of bakend for a selected job's id.
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.unhold_job(jobs)
        self.context.GUI.message("\n".join(result))

    def callback_suspend(self):
        """ Suspend jobs.
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.suspend_job(jobs)
        self.context.GUI.message("\n".join(result))

    def callback_resume(self):
        """ Resume jobs (unsuspend).
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.resume_job(jobs)
        self.context.GUI.message("\n".join(result))

    def callback_reschedule(self):
        """ Reschedule jobs.
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.reschedule_job(jobs)
        self.context.GUI.message("\n".join(result))

    def callback_cancel(self):
        """ Cancel jobs.
        """
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        result = backend.cancel_job(jobs)
        self.context.GUI.message("\n".join(result))

    def callback_edit(self):
        """ Edit jobs.
        """
        from popups import JobEditWindow
        jobs = self.get_selected_items(key=backend.JOB_ID_KEY)
        if jobs:
            self.window = JobEditWindow(jobs)
            self.window.show()


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

    def callback_show_sequence(self):
        import subprocess
        hafarm_parms = self.context.GUI.get_job_parms_from_detail_view()
        picture_parm = hafarm_parms[u'parms'][u'output_picture']
        picture_info = utilities.padding(picture_parm, format="shell")
        picture_path = picture_info[0] 

        config = self.context.config
        viewer = config.select_optional_executable('image_viewer')

        if viewer:
            # Hard coded fix for rv :(
            if viewer.endswith("rv"):
                picture_path = picture_path.replace("*", "#")    
            command = [viewer, picture_path]
            subprocess.Popen(command, shell=False)
            return
        else: 
            self.context.GUI.message("Can't find viewer app in PATH. Trying RV in rez subshell...")

        package = ['rv']
        command = "export HOME=%s; export DISPLAY=:0; rv %s" % (os.getenv("HOME"), picture_path.replace("*", "#"))
        pid = utilities.run_rez_shell(command, package)
        if pid:
            return




#####################################################################
# Tasks view context menu                                           #
#####################################################################

class TasksContextMenu(QMenu, ContextMenuBase):
    def __init__(self, context, position):
        super(self.__class__, self).__init__()
        self.view      = context.views['tasks_view']
        self.model     = context.models['tasks_model']
        self.item_list = ['callback_hold',
                          'callback_unhold',
                          'callback_reschedule',
                          'callback_edit',
                          "",
                          'callback_show_sequence',
                          'callback_show_in_folder',
                          "",
                          'callback_cancel']
        self.context = context
        self.bind_actions(self.build_action_strings(self.item_list))
        self.execute(position)

    def callback_hold(self):
        """ Calls hold command of bakend for a selected job's id.
        """
        jobs = self.get_selected_items(key=backend.TASK_ID_KEY)
        result = backend.hold_job(jobs)
        self.context.GUI.message("\n".join(result))

    def callback_unhold(self):
        """ Calls unhold command of bakend for a selected job's id.
        """
        jobs = self.get_selected_items(key=backend.TASK_ID_KEY)
        result = backend.unhold_job(jobs)
        self.context.GUI.message("\n".join(result))

    def callback_suspend(self):
        """ Suspend jobs.
        """
        jobs = self.get_selected_items(key=backend.TASK_ID_KEY)
        result = backend.suspend_job(jobs)
        self.context.GUI.message("\n".join(result))

    def callback_resume(self):
        """ Resume jobs (unsuspend).
        """
        jobs = self.get_selected_items(key=backend.TASK_ID_KEY)
        result = backend.resume_job(jobs)
        self.context.GUI.message("\n".join(result))

    def callback_reschedule(self):
        """ Reschedule jobs.
        """
        jobs = self.get_selected_items(key=backend.TASK_ID_KEY)
        result = backend.reschedule_job(jobs)
        self.context.GUI.message("\n".join(result))

    def callback_edit(self):
        """ Edit jobs.
        """
        from popups import JobEditWindow
        jobs = self.get_selected_items(key=backend.TASK_ID_KEY)
        if jobs:
            self.window = JobEditWindow(jobs)
            self.window.show()

    def callback_cancel(self):
        """ Cancel jobs.
        """
        jobs = self.get_selected_items(key=backend.TASK_ID_KEY)
        result = backend.cancel_job(jobs)
        self.context.GUI.message("\n".join(result))


    def callback_show_sequence(self):
        import subprocess
        hafarm_parms = self.context.GUI.get_job_parms_from_detail_view()
        picture_parm = hafarm_parms[u'parms'][u'output_picture']
        picture_info = utilities.padding(picture_parm, format="shell")
        picture_path = picture_info[0] 

        config = self.context.config
        viewer = config.select_optional_executable('image_viewer')

        if viewer:
            # Hard coded fix for rv :(
            if viewer.endswith("rv"):
                picture_path = picture_path.replace("*", "#")    
            command = [viewer, picture_path]
            subprocess.Popen(command, shell=False)
            return
        else: 
            self.context.GUI.message("Can't find viewer app in PATH. Trying RV in rez subshell...")

        package = ['rv']
        command = "export HOME=%s; export DISPLAY=:0; rv %s" % (os.getenv("HOME"), picture_path.replace("*", "#"))
        pid = utilities.run_rez_shell(command, package)
        if pid:
            return



    def callback_show_in_folder(self):
        import subprocess
        task_id = self.get_selected_items(key=backend.TASK_NUMBER)[-1]
        hafarm_parms = self.context.GUI.get_job_parms_from_detail_view()
        picture_parm = hafarm_parms[u'parms'][u'output_picture']
        picture_info = utilities.padding(picture_parm, _frame=task_id)
        picture_path = picture_info[0]

        config  = self.context.config
        manager = config.select_optional_executable('file_manager') 

        if not manager:
            self.context.GUI.message("Can't find  file manager.")
            return

        command = [manager, picture_path]
        subprocess.Popen(command, shell=False)



