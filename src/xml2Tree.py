from PyQt4 import QtCore, QtGui, QtXml
from xml.etree.ElementTree import ElementTree
import os

class Tree(QtGui.QTreeWidget):

    def __init__(self, parent):
        # maybe init your data here too
        data = ElementTree()
        f  = open("/tmp/job2.xml")
        xml = f.read()
        f.close()
        data.parse(xml)
        super(Tree, self).__init__(parent)

    def populate(self, data):
        # populate the tree with QTreeWidgetItem items
        for row in data:
            # is attached to the root (parent) widget
            rowItem = QtGui.QTreeWidgetItem(parent)
            rowItem.setText(0, row)
            for subRow in row:
                 # is attached to the current row (rowItem) widget
                 subRowItem = QtGui.QTreeWidgetItem(rowItem)
                 subRowItem.setText(1, subRow)




class XmlHandler(QtXml.QXmlDefaultHandler):
    def __init__(self, root):
        QtXml.QXmlDefaultHandler.__init__(self)
        self._root = root
        self._item = None
        self._text = ''
        self._error = ''

    def startElement(self, namespace, name, qname, attributes):
        if 1 == 1: #qname == 'folder' or qname == 'item':
            if self._item is not None:
                self._item = QtGui.QTreeWidgetItem(self._item)
            else:
                self._item = QtGui.QTreeWidgetItem(self._root)
            self._item.setData(0, QtCore.Qt.UserRole, qname)
            self._item.setText(0, 'Unknown Title')
            if qname == 'folder':
                self._item.setExpanded(True)
            elif 1==1: # qname == 'item':
                self._item.setText(1, attributes.value('type'))
        self._text = ''
        return True

    def endElement(self, namespace, name, qname):
        if 1 == 1: #qname == 'title':
            if self._item is not None:
                self._item.setText(0, self._text)
        else: #qname == 'folder' or qname == 'item':
            self._item = self._item.parent()
        return True

    def characters(self, text):
        self._text += text
        return True

    def fatalError(self, exception):
        print('Parse Error: line %d, column %d:\n  %s' % (
              exception.lineNumber(),
              exception.columnNumber(),
              exception.message(),
              ))
        return False

    def errorString(self):
        return self._error

class Window(QtGui.QTreeWidget):
    def __init__(self):
        QtGui.QTreeWidget.__init__(self)
        self.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.setHeaderLabels(['Variable', 'Value'])
        #source = QtXml.QXmlInputSource()
        data = ElementTree()
        #f  = open("/tmp/job2.xml")
        f  = os.popen("qhost -xml -j")
        data.parse(f)
        #f.close()
        root = data.findall("host")
        self.populate(root)

    def columnCount(self, parent):
        return 2

    def populate(self, data, parent=None):
        if not parent:
            parent = self
        # populate the tree with QTreeWidgetItem items
        for row in data:
            rowItem = QtGui.QTreeWidgetItem(parent)
            if len(row.attrib.keys()): 
                name = row.attrib[row.attrib.keys()[0]]
            else: 
                name = row.tag
            rowItem.setText(0, str(name))
            rowItem.setText(1,str(row.text))
            rowItem.setExpanded(True)
            if len(row.getchildren()) > 1:
                self.populate(row, rowItem)
                                      
            
                   
           
       

if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.resize(400, 300)
    window.show()
    sys.exit(app.exec_())
