from PyQt4.QtGui import *
from PyQt4.QtCore import *
import utilities
import math, os
from constants import *
import utilities

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



class JobsDelegate(QItemDelegate):
    def __init__(self, context, parent=None, *args):
        QItemDelegate.__init__(self, parent, *args)
        self.parent = parent
        self.context = context
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

        self.app_icons = utilities.findIcons()

    def getJobProgress(self, jobid, running_ids):
        pass
                    

    def paint(self, painter, option, index):
        # Icon drawing:
        waiting = index.data(Qt.DecorationRole).toBool()
        if not waiting and index.column() == 2:
            app = None
            jobname = self.parent.root[index.row()][2].text
            if ".hip_" in jobname: app = 'houdini'
            elif ".nk_" in jobname: app = 'nuke'
            elif ".scn_" in jobname: app = 'xsi'
            option = option.__class__(option)
            if app in self.app_icons.keys():
                image = QImage(self.app_icons[app])
                painter.drawImage(option.rect.topLeft(), image)
                option.rect = option.rect.translated(20, 0)    
                QItemDelegate.paint(self, painter, option, index)
                #return

        painter.save()

        # set background color
        painter.setPen(QPen(Qt.NoPen))
        # In case root[] is empty:
        try:
            state = self.parent.root[index.row()][4].text
            jobid = self.parent.root[index.row()][0].text
            tasks_model =  self.context.models['tasks_model']
            running_ids = [x[0].text for x in tasks_model.root]
        except:
            painter.restore()
            return

        # Set job state colors:
        if state in('hqw', 'hRq'):
           painter.setBrush(QBrush(self.hqwC))
        if state == 'qw':
            if jobid in running_ids:
                painter.setBrush(QBrush(self.qwC))
            else:
                painter.setBrush(QBrush(self.qwWaitingC))
        #if state == 'Rr':
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
    
    def createEditor(self, parent, option, index):
        if index.column() == 1:
            sbox = QSpinBox(parent)
            sbox.setSingleStep(100)
            sbox.setRange(-1023, 1024)
            return sbox

    def setEditorData(self, editor, index):    
        item_var = index.data(Qt.DisplayRole)
        item_str = item_var.toPyObject()
        item_int = float(item_str)
        editor.setValue(item_int)

    def setModelData(self, editor, model, index):
        if index.column() == 1:
            job_index= model.index(index.row(), 0)
            job_id   = model.data(job_index).toString()
            data_int = editor.value()
            result = os.popen("qalter -p %s %s" % (data_int, job_id)).read()
            print result



class MachinesDelegate(QItemDelegate):
    def __init__(self, parent=None, *args):
        QItemDelegate.__init__(self, parent, *args)
        self.parent = parent

    def paint(self, painter, option, index):
        painter.save()
        # set background color
        painter.setPen(QPen(Qt.NoPen))

        # Get RAM information:
        tagidx   = utilities.tag2idx(self.parent.root[0], True)
        mem_used = self.parent.root[index.row()][tagidx['mem_used']].text[:-1]
        mem_size = self.parent.root[index.row()][tagidx['mem_used']].text[-1]
        try: 
            mem_used = float(mem_used)
            if mem_size == "M": mem_used /= 1024.0
        except: 
            mem_used = 0.0
        mem_total   = self.parent.root[index.row()][tagidx['mem_total']].text[:-1]
        try: mem_total = float(mem_total)
        except: mem_total = 0.0

        # Load information:
        load_avg = self.parent.root[index.row()][tagidx['load_avg']].text[:-1]
        num_proc = self.parent.root[index.row()][tagidx['num_proc']].text[:-1]
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
