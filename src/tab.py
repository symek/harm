from PyQt4.QtGui import QWidget, QVBoxLayout

class HUI_Tab(QWidget):
    _vboxlayout = None
    def __init__(self, parent):
        super(HUI_Tab, self).__init__(parent)
        parent.addTab(self, "Machines")
        self._vboxlayout = QVBoxLayout(self)