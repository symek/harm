from PyQt4.QtGui import *
from PyQt4.QtCore import *
import utilities
import math, os, hashlib, random
import constants
import utilities


##########################################################
#             Jobs View Delegate                         #
#  - bg colors for states                                #
#  - deletated editor for priority                       #
#  - host_apps icons in Jobs name field                       #
#  - ?                                                   #
##########################################################


class JobsDelegate(QItemDelegate):
    def __init__(self, context, parent=None, *args):
        QItemDelegate.__init__(self, parent, *args)
        self.context = context
        self.model = context.models['jobs_model']
        self.proxy = context.models['jobs_proxy_model']
        self.setColors()
        # TODO: We should not happend in utilities but config more likely:
        self.app_icons = utilities.findIcons(context.config['HARM_ICON'])

        self.header = {}
        # self.header['pending'] = 'progress'
        self.header['r']       = 'rendering'
        self.header['cdb']     = 'archive'
        self.header['Rr']      = 're-render'
        self.header['qw']      = 'waiting'
        self.header['hqw']     = 'on hold'


    def setColors(self):
        '''TODO: to be moved into Config() control'''
        self.waitingC = QColor()
        self.progresC = QColor()
        self.finisheC = QColor()
        self.selectedC= QColor()
        self.selectedC.setHsvF(0.108, 0.95, 1)
        self.waitingC.setHsvF(0.30, 0.3, 1)
        self.progresC.setHsvF(0.0, 0.2, 1)
        self.finisheC.setHsvF(0.69, 0.2, 1)
        self.hqwC = QColor()
        self.hqwC.setHsvF(.15, .2, 1)
        self.qwC = QColor()
        self.qwC.setHsvF(.30, .2, 1)
        self.qwWaitingC = QColor()
        self.qwWaitingC.setHsvF(.6, .2, 1)


    def getJobProgress(self, jobid, running_ids):
        pass
                    

    def paint(self, painter, option, index):
        # Icon drawing:
        host_app     = None
        waiting      = index.data(Qt.DecorationRole).toBool()
        job_name_idx = self.model.get_key_index("NAME")
        s_index      = self.proxy.mapToSource(index)
        running_ids  = []

        painter.save()
        if not waiting and index.column() == job_name_idx:
            job_name     = self.model._data[s_index.row()][job_name_idx]
            if ".hip_" in job_name:   host_app = 'houdini'
            elif ".nk_" in job_name:  host_app = 'nuke'
            elif ".scn_" in job_name: host_app = 'xsi'

            option = option.__class__(option) #?
            if host_app in self.app_icons.keys():
                image = QImage(self.app_icons[host_app])
                painter.drawImage(option.rect.topLeft(), image)
                option.rect = option.rect.translated(20, 0)    
                QItemDelegate.paint(self, painter, option, index)
                #return


        # set background color
        painter.setPen(QPen(Qt.NoPen))
        # FIXME: This should not be nesecery?
        if self.model._data:
            try:
                state_idx = self.model.get_key_index("STATE")
                jobid_idx = self.model.get_key_index("ARRAY_JOB_ID")
                state = self.model._data[s_index.row()][state_idx]
                jobid = self.model._data[s_index.row()][jobid_idx]

                tasks_model =  self.context.models['tasks_model']
                tasks_idx   = tasks_model.get_key_index("ARRAY_JOB_ID")
                # FIXME: Presence of state columns indicates tasks are running (not taken from DB)
                is_running  = tasks_model.get_key_index("ARRAY_JOB_ID")
                running_ids = [x[tasks_idx] for x in tasks_model._data]
            except:
                pass
        else:
            painter.restore()
            return

        # Set job state colors:
        if state in ('PENDING', 'CANCELED'):
            painter.setBrush(QBrush(self.hqwC))
        elif state in ("PENDING",):
            painter.setBrush(QBrush(self.qwWaitingC))
        elif jobid.strip() in running_ids and is_running:
            painter.setBrush(QBrush(self.qwC))
        else:
            pass
            # painter.setBrush(QBrush(QColor(Qt.white)))

        # Set background for selected objects:
        if option.state & QStyle.State_Selected:
            painter.setBrush(QBrush(self.selectedC))


        painter.drawRect(option.rect)
        painter.setPen(QPen(Qt.black))
        value = index.data(Qt.DisplayRole)

        if value.isValid():
            text = value.toString()
            if text in self.header.keys():
                text = self.header[str(text)]
            painter.drawText(option.rect, Qt.AlignLeft, text)

        painter.restore()
        
    
    def createEditor(self, parent, option, index):
        priority_idx = self.model.get_key_index("JAT_prio")
        if index.column() == priority_idx:
            sbox = QSpinBox(parent)
            sbox.setSingleStep(100)
            sbox.setRange(-1023, 1024)
            return sbox

    def setEditorData(self, editor, index):    
        item_var = index.data(Qt.DisplayRole)
        item_str = item_var.toPyObject()
        if not item_str: item_str = "0"
        item_int = float(item_str)
        editor.setValue(item_int)

    def setModelData(self, editor, model, index):
        priority_idx = self.model.get_key_index("JAT_prio")
        jobid_idx    = self.model.get_key_index("JB_job_number")
        # TODO: Don't call popen unless data was actually changed. 
        if index.column() == priority_idx:
            job_index= model.index(index.row(), jobid_idx)
            job_id   = model.data(job_index).toString()
            data_int = editor.value()
            result = os.popen("qalter -p %s %s" % (data_int, job_id)).read()
            print result


##########################################################
#             Machines View Delegate                      #
#  - bg colors for machines load                         #
#  - ?                                                   #
##########################################################

class MachinesDelegate(QItemDelegate):
    def __init__(self, context, parent=None, *args):
        QItemDelegate.__init__(self, parent, *args)
        self.parent = parent
        self.context = context
        self.model   = context.models['machine_model']
        self.proxy   = context.models['machine_proxy_model']

    def paint(self, painter, option, index):
        painter.save()
        # # set background color
        painter.setPen(QPen(Qt.NoPen))

        # # Get RAM information:
        s_index      = self.proxy.mapToSource(index)
        mem_used_idx = self.model.get_key_index("AllocMem")
        mem_free_idx = self.model.get_key_index("FreeMem")
        mem_real_idx = self.model.get_key_index("RealMemory")

        mem_used = self.model._data[s_index.row()][mem_used_idx]
        mem_free = self.model._data[s_index.row()][mem_free_idx]
        mem_real = self.model._data[s_index.row()][mem_real_idx]

        if mem_used.isdigit(): mem_used = int(mem_used)
        else: mem_used = 0
        if mem_real.isdigit(): mem_real = int(mem_real)
        else:     mem_real = 0


        # # Load information:
        # load_avg_idx = self.model.get_key_index("load_avg")
        # num_proc_idx = self.model.get_key_index("num_proc")
        # load_avg = self.model._data[s_index.row()][load_avg_idx]
        # num_proc = self.model._data[s_index.row()][num_proc_idx]
        # try: load_avg = float(load_avg)
        # except: load_avg = 0.0
        # try: num_proc = float(num_proc)
        # except: num_proc = 1.0
        
        
        # # Set color based on ram and load:
        # # TODO: Color setting should come from confing file or user condiguration!
        if mem_used and mem_real:
            color = QColor()
            sat = utilities.clamp(mem_used/mem_real, 0.0, 1.0)
            sat = utilities.fit(sat, 0.0, 1.0, 0.1, 0.85)
            hue = 1.0 #utilities.clamp(load_avg/num_proc, 0.0, 1.0)
            hue = utilities.fit(hue, 0.0, 1.0, .25, .9)
            color.setHsvF(hue, sat , 1)
            # Mark in red hosts with used ram above 0.9 (or other SGE_HOST_RAM_WARNING constant)
            # if mem_used > mem_real * constants.SGE_HOST_RAM_WARNING:
            #     color.setHsvF(1, 1 , 1)
            painter.setBrush(QBrush(color))

        # # Set selection color:
        if option.state & QStyle.State_Selected:
            painter.setBrush(QBrush(Qt.gray))
        painter.drawRect(option.rect)

        painter.setPen(QPen(Qt.white))
        value = index.data(Qt.DisplayRole)
        if value.isValid():
            text = value.toString()
            painter.drawText(option.rect, Qt.AlignLeft, text)

        painter.restore()




#################### Old stuff ################################################


class TasksDelegate(QItemDelegate):
    def __init__(self, context, parent=None, *args):
        QItemDelegate.__init__(self, parent, *args)
        self.machine_background = QColor()
        self.context = context
        self.model   = context.models['tasks_model']
        self.proxy   = context.models['tasks_proxy_model']
        self.colorize_style = 0
        self.setColors()

        self.header = {}
        self.header['pending'] = 'progress'
        self.header['r']       = 'rendering'
        self.header['cdb']     = 'archive'
        self.header['Rr']      = 're-render'
        self.header['qw']      = 'waiting'
        self.header['hqw']     = 'on hold'
        self.header['ds']      = 'deleted'
        self.header['dS']      = 'suspended'
        self.header['hr']      = 'holded'


        self.wallclock_idx = None
        self.maxvmem_idx   = None

        self.min_wallclock = 0
        self.avg_wallclock = 0
        self.max_wallclock = 0

        self.min_maxvmem   = 0
        self.avg_maxvmem   = 0
        self.max_maxvmem   = 0
        self.job_id        = None
        self.machines      = {}

        # User wants to colorize taskes based on performance statistics:
        if self.colorize_style == 1:
            self.colorize      = self.compute_stats()
        # User wants to colorize based on hostname:
        elif self.colorize_style == 2:
            self.colorize = True
        # 
        else:
            self.colorize      = False

    def compute_stats(self):
        """ Computes basics statistics (min, max, avg) of a tasks model.
        Note: we assume that 'self' displays tasks from a single job atm.
        """
        if not self.model._data:
            return False
        # Fields indices:
        self.maxvmem_idx   = self.model.get_key_index("mem")
        self.wallclock_idx = self.model.get_key_index("ru_utime")
        # Return if they are not there:
        if not self.maxvmem_idx or not self.wallclock_idx:
            return False

        maxvmem            = self.get_array(self.model._data, self.maxvmem_idx)
        self.min_maxvmem   = min(maxvmem)
        self.avg_maxvmem   = sum(maxvmem)/len(maxvmem)
        self.max_maxvmem   = max(maxvmem)

        wallclock          = self.get_array(self.model._data, self.wallclock_idx)
        self.min_wallclock = min(wallclock)
        self.avg_wallclock = sum(wallclock)/len(wallclock)
        self.max_wallclock = max(wallclock)

        self.job_id_idx    = self.model.get_key_index("JB_job_number")
        self.job_id        = self.model._data[0][self.job_id_idx]

        if DEBUG:
            print "maxvmem:"
            print "min: " + str(self.min_maxvmem)
            print "avg: " + str(self.avg_maxvmem)
            print "max: " + str(self.max_maxvmem)

            print "wallclock:"
            print "min: " + str(self.min_wallclock)
            print "avg: " + str(self.avg_wallclock)
            print "max: " + str(self.max_wallclock)

        return True

    def setColors(self):
        '''TODO: to be moved into Config() control'''
        self.waitingC = QColor()
        self.progresC = QColor()
        self.finisheC = QColor()
        self.selectedC= QColor()
        self.selectedC.setHsvF(0.108, 0.95, 1)
        self.waitingC.setHsvF(0.30, 0.3, 1)
        self.progresC.setHsvF(0.0, 0.2, 1)
        self.finisheC.setHsvF(0.69, 0.2, 1)

        self.hqwC = QColor()
        self.hqwC.setHsvF(.15, .2, 1)
        self.qwC = QColor()
        self.qwC.setHsvF(.30, .2, 1)
        self.qwWaitingC = QColor()
        self.qwWaitingC.setHsvF(.6, .2, 1)


    def get_machines_color(self):
        view = self.context.views['machines_view']

    def get_array(self, data, index, convert=True):
        """Returns agragated array of columns (i.e. transpose).
        Optionally converts values to numbers.
        """
        result = []
        # Early return for non indices:
        if not index:
            return [0]
        for item in data:
            item = item[index]
            if convert:
                item = utilities.to_number(item)
            result.append(item)
        return result


    
    def paint(self, painter, option, index):
        painter.save()
        wallclock = None
        maxvmem   = None
        failed    = 0
        # Proxy to actual model:
        s_index = self.proxy.mapToSource(index)

        if self.model._data:
            # Find our job_id and compare it with previous one (if any):
            job_id_idx = self.model.get_key_index("JOBID")
            status_idx = self.model.get_key_index("STATUS")
            job_id     = self.model._data[s_index.row()][job_id_idx]
            status     = self.model._data[s_index.row()][status_idx]
            if status == "PENDING":
                painter.setBrush(QBrush(self.waitingC))
                painter.restore()
                return

            # recompute job stats only on recently updated model: 
            # if job_id != self.job_id and self.colorize_style == 1:
            #     self.job_id   = job_id
            #     self.colorize = self.compute_stats()
        else:
            painter.restore()
            return

        # # Get values for current task:
        # # TODO: This should happen for a single index per row...
        # try:
        #     failed        = self.model._data[s_index.row()][failed_idx]
        #     wallclock     = self.model._data[s_index.row()][self.wallclock_idx]
        #     maxvmem       = self.model._data[s_index.row()][self.maxvmem_idx]
        #     maxvmem       = utilities.to_number(maxvmem)
        # except:
        #     pass
        #     #print "No wallclock no maxvmem for current index."

        painter.setPen(QPen(Qt.NoPen))
        color = QColor()
        # # Colorize tasks based on its relative cpu/ram cost:
        # if wallclock and maxvmem and self.colorize and self.colorize_style == 1:
        #     sat = utilities.fit(float(maxvmem),   self.min_maxvmem,   self.max_maxvmem, 0.05, 0.65)
        #     hue = utilities.fit(float(wallclock), self.min_wallclock, self.max_wallclock, 0.25, 0.9)
        #     color.setHsvF(hue, sat, 1)

        # # based on hostname:
        # elif self.colorize and self.colorize_style == 2:
        #     hostname_idx = self.model.get_key_index("hostname")
        #     if hostname_idx:
        #         hostname = self.model._data[s_index.row()][hostname_idx]
        #         if not hostname in self.machines:
        #             # We take first three digits of md5 hash as a seed for random color:
        #             random_digit = int(str(int(hashlib.md5(hostname).hexdigest(),16))[:3])
        #             self.machines[hostname] = random_digit
        #         # Random color per hostname:
        #         random.seed(self.machines[hostname])
        #         color.setHsvF(random.random(), 0.3, 1)
        # else:
        #     color = QColor(Qt.white)

        # # Set backgroud color:
        painter.setBrush(QBrush(color))

        # # TODO:
        # # Mark in red tasks with failed status:
        # #if failed != 0:
        # #    color.setHsvF(1, .5, 1)


        # Set background for selected objects:
        if option.state & QStyle.State_Selected:
            painter.setBrush(QBrush(self.selectedC))

        painter.drawRect(option.rect)
        painter.setPen(QPen(Qt.black))
        value = index.data(Qt.DisplayRole)

        if value.isValid():
            text = value.toString()
            if text in self.header.keys():
                text = self.header[str(text)]
            painter.drawText(option.rect, Qt.AlignLeft, text)

        painter.restore()



class JobDelegate(QStyledItemDelegate):
    def __init__(self, context, parent=None, *args):
        QItemDelegate.__init__(self, parent, *args)
        self.parent = parent
        self.context = context
        self.waitingC = QColor()
        self.progresC = QColor()
        self.finisheC = QColor()
        self.selectedC= QColor()
        self.selectedC.setHsvF(0.108, 0.2, 1)
        self.waitingC.setHsvF(0.30, 0.3, 1)
        self.progresC.setHsvF(0.0, 0.2, 1)
        self.finisheC.setHsvF(0.69, 0.2, 1)
        self.hqwC = QColor()
        self.hqwC.setHsvF(.15, .2, 1)

        self.qwC = QColor()
        self.qwC.setHsvF(.30, .2, 1)
        self.qwWaitingC = QColor()
        self.qwWaitingC.setHsvF(.6, .2, 1)

    def getJobProgress(self, jobid, running_ids):
        pass            

    def paint(self, painter, option, index):
        painter.save()

        # set background color
        painter.setPen(QPen(Qt.NoPen))
        # In case root[] is empty:
        #try:
        token = self.parent.mydata[index.row()][0]
        print token
        #except:
        #    painter.restore()
        #    return

        # Set job state colors:
        if token in ('JAT_task_number',) :
           painter.setBrush(QBrush(self.hqwC))
        if token in ('cpu', 'mem', 'io', 'vmem', 'maxvmem'):       
            painter.setBrush(QBrush(self.qwC))
        if token.isupper():
            painter.setBrush(QBrush(Qt.gray))
        #    color = QColor()
        #    color.setHsvF(.45, .3, 1)
        #    painter.setBrush(QBrush(color))
            
        if option.state & QStyle.State_Selected:
            painter.setBrush(QBrush(self.selectedC))

        #TODO Set job progress gradient:
        if index.column() == 765432: # TODO: change it to 2 to enable this part           
            grad   = QLinearGradient(QPointF(0,.2), QPointF(1, .2))
            grad.setCoordinateMode(2)
            grad.setColorAt(0.0, self.waitingC)
            grad.setColorAt(0.5, self.waitingC)
            grad.setColorAt(.51, self.progresC)
            grad.setColorAt(.75, self.progresC)
            grad.setColorAt(.76, self.finisheC)
            grad.setColorAt(1.0, self.finisheC)
            brush  = QBrush(grad)
            painter.setBrush(brush)



        painter.drawRect(option.rect)
        painter.setPen(QPen(Qt.black))
        value = index.data(Qt.DisplayRole)
        if value.isValid():
            text = value.toString()
            painter.drawText(option.rect, Qt.AlignLeft, text)

        painter.restore()


 # #TODO Set job progress gradient:
 #        if index.column() == 765432: # TODO: change it to 2 to enable this part           
 #            grad   = QLinearGradient(QPointF(0,.2), QPointF(1, .2))
 #            grad.setCoordinateMode(2)
 #            grad.setColorAt(0.0, self.waitingC)
 #            grad.setColorAt(0.5, self.waitingC)
 #            grad.setColorAt(.51, self.progresC)
 #            grad.setColorAt(.75, self.progresC)
 #            grad.setColorAt(.76, self.finisheC)
 #            grad.setColorAt(1.0, self.finisheC)
 #            brush  = QBrush(grad)
 #            painter.setBrush(brush)



