#!/usr/bin/python
import os, sys
from PyQt4.QtCore  import *
from PyQt4.QtGui   import *
from PyQt4.QtGui   import QIcon
from PyQt4         import QtGui
from GUI           import *
from constants     import *


class HarmMainWindow(QMainWindow, HarmMainWindowGUI):
    def __init__(self, xml, app, splash,  *args):
        QWidget.__init__(self, *args)
        # Basics:
        self.setGeometry(0,0, 1200,750)
        self.setWindowTitle("Human Ark Resource Manager")
        self.setWindowIcon(QIcon("icon.png"))
        self.resize(1200,750)
        #self.setMinimumSize(500,650)
        self.app = app
        self.splash = splash

        self.setupGUI(init=True)
        self.setupSLOTS()
    
       
    def setupSLOTS(self):
        # Update Job View SIGNAL:
        self.connect(self.jobs_view, SIGNAL("clicked(const QModelIndex&)"),  
                     self.jobs_view_clicked)
        self.connect(self.finished_view, SIGNAL("clicked(const QModelIndex&)"),  
                     self.finished_view_clicked)
        self.connect(self.tasks_view, SIGNAL("clicked(const QModelIndex&)"),  
                     self.tasks_view_clicked)
        self.connect(self.right_tab_widget, SIGNAL("currentChanged(const int&)"),  
                     self.update_std_views)
        self.connect(self.refreshAction, SIGNAL('triggered()'), 
                     self.refreshAll)
        self.connect(self.job_view_combo, SIGNAL('currentIndexChanged(int)'), 
                     self.change_job_view)
        self.connect(self.machine_view_combo, SIGNAL('currentIndexChanged(int)'), 
                     self.change_machine_view)
        self.connect(self.jobs_filter_line, SIGNAL('textChanged(const QString&)'),\
                     self.set_jobs_proxy_model_wildcard)   
        self.connect(self.tasks_onlySelected_toggle, SIGNAL('stateChanged(int)'),\
                     self.set_tasks_proxy_model_filter)   
        #self.connect(self.job_details_filter_line, SIGNAL('textChanged(const QString&)'),\
        #             self.set_job_detail_proxy_model_wildcard)  
    

def main():
    xml = os.popen(SGE_JOBS_LIST_GROUPED)
    #xml = "/tmp/jobs.xml"

    app = QApplication(sys.argv)
    #app.setStyle(QtGui.QStyleFactory.create("Oxygen"))
    splash_pix = QPixmap('/STUDIO/scripts/harm/icons/head.jpg')
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    #splash.setMask(splash_pix.mask())
    splash.show()
    splash.showMessage("Reading SGE details...")
    app.processEvents()
    w = HarmMainWindow(xml, app, splash)
    # Apply stype sheets:
    #f = open("/home/symek/Downloads/darkorange.stylesheet")
    #w.setStyleSheet(f.read())
    #f.close()
    splash.finish(w)
    w.show()
   
    sys.exit(app.exec_())





if __name__ == "__main__": main()
