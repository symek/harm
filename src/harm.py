#!/usr/bin/python
import os, sys, time
from PyQt4.QtCore  import *
from PyQt4.QtGui   import *
from PyQt4.QtGui   import QIcon
from PyQt4         import QtGui
from GUI           import *
from constants     import *

from plugin import PluginManager
import config
import server
import tabs

class Severity(object):
    low  = 0
    mid  = 1
    high = 2


class HarmMainWindow(QMainWindow, HarmMainWindowGUI):
    auto_update_views = []
    def __init__(self, _config, app, splash,  *args):
        QWidget.__init__(self, *args)
        # Basics:
        self.setGeometry(0,0, 1200,750)
        self.setWindowTitle("Human Ark Resource Manager")
        self.setWindowIcon(QIcon("icon.png"))
        self.resize(1200,750)
        self.tab_manager = PluginManager()
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
        self.timer.timeout.connect(self.autoRefresh)
        self.timer.start()

    def splashMessage(self, text):             
        self.splash.showMessage(text, Qt.AlignBottom)
        self.app.processEvents()

    def message(self, text, severity=Severity.low):
        view  = self.context.views['job_detail_basic_view']
        view.setPlainText(text)


def main():

    # App setup:
    app     = QApplication(sys.argv)
    # app.setStyle(QtGui.QStyleFactory.create("Oxygen"))
    _config = config.Config()
    
    # Splash setup:
    splash_pix = QPixmap(_config.get_harm_path('head.jpg', "HARM_ICON"))
    splash     = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.show()
    splash.showMessage("Reading SGE details...")
    app.processEvents()

    window = HarmMainWindow(_config, app, splash)
    window.server = server.BackendServer()
    window.server.start()

    style_path = _config.get_harm_path('darkorange.stylesheet', "HARM_ICON")
    # Apply stype sheets:
    with open(style_path) as file:
        window.setStyleSheet(file.read())
    splash.finish(window)


    # Show main window:
    window.show()
    sys.exit(app.exec_())
    window.server.terminate()

if __name__ == "__main__": main()
