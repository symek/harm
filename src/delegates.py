from PyQt4.QtGui import *
from PyQt4.QtCore import *
import utilities
import math, os
from constants import *
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
        self.app_icons = utilities.findIcons()

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
        job_name_idx = self.model.get_key_index("JB_name")
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
                state_idx = self.model.get_key_index("state")
                jobid_idx = self.model.get_key_index("JB_job_number")
                state = self.model._data[s_index.row()][state_idx]
                jobid = self.model._data[s_index.row()][jobid_idx]

                tasks_model =  self.context.models['tasks_model']
                tasks_idx   = tasks_model.get_key_index("JB_job_number")
                running_ids = [x[tasks_idx] for x in tasks_model._data]
            except:
                pass
        else:
            painter.restore()
            return

        # Set job state colors:
        if state in('hqw', 'hRq'):
            painter.setBrush(QBrush(self.hqwC))
        elif state == 'cdb':
            painter.setBrush(QBrush(QColor(Qt.white)))
        elif state in ('qw', 'Rq'):
            if jobid.strip() in running_ids:
                painter.setBrush(QBrush(self.qwC))
            else:
                painter.setBrush(QBrush(self.qwWaitingC))

        # Set background for selected objects:
        if option.state & QStyle.State_Selected:
            painter.setBrush(QBrush(self.selectedC))


        painter.drawRect(option.rect)
        painter.setPen(QPen(Qt.black))
        value = index.data(Qt.DisplayRole)

        if value.isValid():
            text = value.toString()
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
        # set background color
        painter.setPen(QPen(Qt.NoPen))

        # Get RAM information:
        s_index      = self.proxy.mapToSource(index)
        mem_used_idx = self.model.get_key_index("mem_used")
        mem_size_idx = self.model.get_key_index("mem_size")
        mem_used = self.model._data[s_index.row()][mem_used_idx][:-1]
        mem_size = self.model._data[s_index.row()][mem_used_idx][-1]
        try: 
            mem_used = float(mem_used)
            if mem_size == "M": mem_used /= 1024.0
        except: 
            mem_used = 0.0

        mem_total_idx= self.model.get_key_index("mem_total")
        mem_total    = self.model._data[s_index.row()][mem_total_idx][:-1]
        try: mem_total = float(mem_total)
        except: mem_total = 0.0

        # Load information:
        load_avg_idx = self.model.get_key_index("load_avg")
        num_proc_idx = self.model.get_key_index("num_proc")
        load_avg = self.model._data[s_index.row()][load_avg_idx]
        num_proc = self.model._data[s_index.row()][num_proc_idx]
        try: load_avg = float(load_avg)
        except: load_avg = 0.0
        try: num_proc = float(num_proc)
        except: num_proc = 1.0
        
        
        # Set color based on ram and load:
        # TODO: Color setting should come from confing file or user condiguration!
        if mem_used and mem_total:
            color = QColor()
            sat = utilities.clamp(mem_used/mem_total, 0.0, 1.0)
            sat = utilities.fit(sat, 0.0, 1.0, 0.1, 0.85)
            hue = utilities.clamp(load_avg/num_proc, 0.0, 1.0)
            hue = utilities.fit(hue, 0.0, 1.0, .25, .9)
            color.setHsvF(hue, sat , 1)
            # Mark in red hosts with used ram above 0.9 (or other SGE_HOST_RAM_WARNING constant)
            if mem_used > mem_total * SGE_HOST_RAM_WARNING:
                color.setHsvF(1, 1 , 1)
            painter.setBrush(QBrush(color))

        # Set selection color:
        if option.state & QStyle.State_Selected:
            painter.setBrush(QBrush(Qt.gray))
        painter.drawRect(option.rect)

        painter.setPen(QPen(Qt.black))
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
        self.machines_color = 0


    def get_machines_color(self):
        view = self.context.views['machines_view']
       
    
    def paint(self, painter, option, index):
        painter.save()

        if index.column() == 6:
            machine = self.context.models['tasks_proxy_model'].data(index)
            machine = machine.toString()

        painter.drawRect(option.rect)
        painter.setPen(QPen(Qt.black))
        value = index.data(Qt.DisplayRole)
        if value.isValid():
            text = value.toString()
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



