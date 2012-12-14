#!/usr/bin/python
import os, sys, time
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

        # Timer:
        self.tick = time.time()

        self.timer = QTimer()
        # FIXME: This should configurable also:
        # FIXME: Auto-update should be disabled when ever 
        # user has selected job in cdb state (from database)
        self.timer.setInterval(1000*120) # update once for 2 minute .
        self.timer.timeout.connect(self.refreshAll)
        self.timer.start()


    def splashMessage(self, text):             
        self.splash.showMessage(text, Qt.AlignBottom)
        self.app.processEvents()

    def tick_tack(self):
        from time import time
        self.tick = time()
    

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
