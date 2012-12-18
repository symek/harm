#!/usr/bin/python
import os, sys, time
from PyQt4.QtCore  import *
from PyQt4.QtGui   import *
from PyQt4.QtGui   import QIcon
from PyQt4         import QtGui
from GUI           import *
from constants     import *
import config


class HarmMainWindow(QMainWindow, HarmMainWindowGUI):
    def __init__(self, _config, app, splash,  *args):
        QWidget.__init__(self, *args)
        # Basics:
        self.setGeometry(0,0, 1200,750)
        self.setWindowTitle("Human Ark Resource Manager")
        self.setWindowIcon(QIcon("icon.png"))
        self.resize(1200,750)
        #self.setMinimumSize(500,650)
        self.app    = app
        self.splash = splash
        self.config = _config

        self.setupGUI(init=True)
        self.setupSLOTS()

        self.timer = QTimer()
        # FIXME: Auto-update should be disabled when ever 
        # user has selected job in cdb state (from database)
        # FIXME: This is experimental notation:
        interval = self.config.get_value("HarmMainWindow/timer/setInterval")
        self.timer.setInterval(interval)
        self.timer.timeout.connect(self.refreshAll)
        self.timer.start()


    def splashMessage(self, text):             
        self.splash.showMessage(text, Qt.AlignBottom)
        self.app.processEvents()

def main():

    # App setup:
    app     = QApplication(sys.argv)
    _config = config.Config()
    
    # Splash setup:
    splash_pix = QPixmap(_config.get_harm_path('head.jpg', "HARM_ICON"))
    splash     = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.show()
    splash.showMessage("Reading SGE details...")
    app.processEvents()
    w = HarmMainWindow(_config, app, splash)
    splash.finish(w)
    # Show main window:
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__": main()
    #app.setStyle(QtGui.QStyleFactory.create("Oxygen"))
    # Apply stype sheets:
    #f = open("/home/symek/Downloads/darkorange.stylesheet")
    #w.setStyleSheet(f.read())
    #f.close()
