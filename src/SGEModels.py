from PyQt4.QtCore import *
from PyQt4 import QtGui
from xml.etree.ElementTree import ElementTree
import tokens
import utilities
import time


from PyQt4.QtGui import *
from PyQt4.QtCore import *

class SGEListModel2(QAbstractTableModel, ElementTree):
    #FIXME: Merge it with SGETableModel
    def __init__(self, xml=None, entry="job_info", parent=None, *args):
        super(SGEListModel2, self).__init__()
        self.mydata = []

        if entry:
            self.entry = entry
        if xml and entry:        
            self.xml = xml
            #try:
            self.parse(xml)
            self.root = self.find(self.entry)
            self.mydata = []
            self.mydata = self.find_req(self.root, self.mydata)
        else:
            self.root = []

    def find_req(self, tree, storage):
        children = tree.getchildren()
        for child in range(len(children)):
            if children[child].text:
                if len(children[child].text.strip()) == 0:
                    self.find_req(children[child], storage)
            elif not children[child].text:
                self.find_req(children[child], storage)
            if  children[child].text:
                if  children[child].tag in ("VA_variable", "UA_name"): 
                    tag  = children[child].text
                    text =  children[utilities.clamp(child+1, 0, len(children)-1)].text
                elif children[child].tag in ("VA_value", "UA_value"):
                    pass
                else: 
                    tag  = children[child].tag
                    text = children[child].text
                if len(text.strip()) > 0 and (tag, text.strip()) not in storage:
                    storage.append((tag, text.strip()))
        return storage
        
    def setRoot(entry):
        self.root = self.find(entry)

    def update(self, xml, entry=None):
        if entry: 
            self.entry = entry
        self.xml = xml
        #try:
        self.parse(xml)
        self.root = self.find(self.entry)
        self.mydata = []
        self.mydata = self.find_req(self.root, self.mydata)
        
    def rowCount(self, parent):
        return len(self.mydata)

    def columnCount(self, parent):
        if len(self.mydata) > 0:
            return len(self.mydata[0]) - 1
        else:
            return 0

    def data(self, index, role):
        #FIXME: Using hard link with Element Tree disallows any sorting...
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        # Read element from a elementTree sub-entry:
        value = self.mydata[index.row()][1]
        # Process data: 
        if not value: 
            return QVariant() 
        if value.isdigit(): 
            value = int(value)
        try: 
            value = float(value)
        except: 
            pass
        # Finally return something meaningfull:
        return QVariant(value)


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:        
            tokens = ("Name", "Value")
            return QVariant(tokens[section])
        elif orientation == Qt.Vertical:
            section = utilities.clamp(section, 0, len(self.mydata))
            return self.mydata[section][0]
        return QVariant("Value")








class SGEListModel(QAbstractTableModel, ElementTree):
    #FIXME: Merge it with SGETableModel
    def __init__(self, xml=None, entry="job_info", parent=None, *args):
        super(SGEListModel, self).__init__()
        if entry:
            self.entry = entry
        if xml and entry:        
            self.xml = xml
            self.parse(xml)
            self.root = self.find(entry)
        else:
            self.root = []
        
    def setRoot(entry):
        self.root = self.find(entry)

    def update(self, xml, entry=None):
        if entry: 
            self.entry = entry
        self.xml = xml
        self.parse(xml)
        self.root = self.find(self.entry)
        
    def columnCount(self, parent):
        return len(self.root)

    def rowCount(self, parent):
        if len(self.root):
            return len(self.root[0])
        else:
            return 0

    def data(self, index, role):
        #FIXME: Using hard link with Element Tree disallows any sorting...
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        # Read element from a elementTree sub-entry:
        value = self.root[index.column()][index.row()].text
        # Process data: 
        if not value: 
            return QVariant() 
        if value.isdigit(): 
            value = int(value)
        try: 
            value = float(value)
        except: 
            pass
        # Finally return something meaningfull:
        return QVariant(value)


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation != Qt.Horizontal:        
           #if len(self.root[0]) < section:
               #print "Avoiding out of root section"
            return QVariant(self.root[0][section].tag)
        return QVariant("Value")



class SGETableModel(QAbstractTableModel):
    '''Accomodates ElementTree object into QAbstractTableModel.
            -xml is either a /path/to/file.xml or file-like object.
            -entry root point of a xml file. Rest of the body 
       is a stuff required by QtTableWidget display.'''
    def __init__(self, xml=None, entry=["job_info"], parent=None, attrib=False, *args):
        super(SGETableModel, self).__init__()
        self.tree = ElementTree()
        if entry:
            self.entry = entry
        if xml and entry:
            self.xml = xml
            try:
                self.tree.parse(xml)
            except:
                print "Can't parse xml"
                return
            self.root = self.agregate(self.entry)
        self.attrib = attrib


    def agregate(self, entry):
        # Agragate xml branches into a single list:
        _l = []
        for token in entry:
            elements = self.tree.find(token)
            if elements != None:
                for item in elements:
                    if item != None:
                        _l.append(item)
        return _l

    def setRoot(self, entry):
        self.root = self.tree.find(entry)

    def setTree(self, tree):
        self.root = tree

    def reduce(self, entry):
        self.root = self.tree.findall(entry)

    def flags(self, index):
        flag = super(SGETableModel, self).flags(index)
        return flag | Qt.ItemIsEditable

    def update(self, xml, entry=None):
        if entry: 
            self.entry = entry
        self.xml = xml
        try:
            self.tree.parse(xml)
            self.root = self.agregate(self.entry)
        except:
            a         = []
            self.root = []
            self.root.append(a)
            
    def columnCount(self, parent):
        if len(self.root):
            return len(self.root[0])
        else:
            return 0

    def rowCount(self, parent):
        if len(self.root):
            return len(self.root)
        else:
            return 0

    def data(self, index, role):
        #FIXME: Using hard link with Element Tree disallows any sorting...
        if not index.isValid():
            return QVariant()
        #elif role == Qt.DecorationRole and index.column() == 0:
        #    return QColor(Qt.red)
        elif role != Qt.DisplayRole:
            return QVariant()

        # Read element from a elementTree sub-entry:
        value = self.root[index.row()][index.column()].text

        # Change time string formating:
        if self.root[index.row()][index.column()].tag in tokens.time_strings: 
            value = self.parse_time_string(value)

        # Shorten machine name in Tasks view:
        if self.root[index.row()][index.column()].tag == 'queue_name':
            if value: 
                value = value.split("@")[-1]
                if "." in value:
                    value = value.split(".")[0]

        # Process data: 
        if not value: 
            return QVariant() 
        if value.isdigit(): 
            value = int(value)
        try: 
            value = float(value)
        except: 
            pass
        # Finally return something meaningfull:
        return QVariant(value)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        def header_replace(name):
            if name in tokens.header.keys():
                name = tokens.header[name]
            return name

        if role != Qt.DisplayRole:
            return QVariant()

        if orientation == Qt.Horizontal:
            if self.attrib:
              return QVariant(header_replace(self.root[0][section].attrib['name']))        
            return QVariant(header_replace(self.root[0][section].tag))

        elif orientation == Qt.Vertical:
            if self.attrib:
                return QVariant(header_replace(self.root[section].attrib['name']))
            return QVariant(header_replace(int(section+1)))

    def parse_time_string(self, time):
        date, time = time.split("T")
        return " ".join((time, date))


    
class SGETreeView(QtGui.QTreeWidget):
    def __init__(self, xml=None, entry="djob_info"):
        QtGui.QTreeWidget.__init__(self)
        self.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.setHeaderLabels(['Variable', 'Value'])
        self.data = ElementTree()
        self.data.parse(xml)
        self.entry = entry
        self.root = self.data.find(self.entry)
        self.populate(self.root)

    def update(self, xml):
        self.data = ElementTree()
        self.data.parse(xml)
        self.root = self.data.find(self.entry)
        #self.rowsRemoved(QModelIndex(), 0, len(self.root))
        self.populate(self.root)        

    def columnCount(self, parent):
        return 2

    def populate(self, data, parent=None):
        if not parent:
            parent = self
        # populate the tree with QTreeWidgetItem items
        for row in data:
            rowItem = QtGui.QTreeWidgetItem(parent)
            rowItem.setText(0, str(row.tag))
            rowItem.setExpanded(True)
            # is attached to the root (parent) widget
            for child in row.getchildren():
                # is attached to the current row (rowItem) widget
                childItem = QtGui.QTreeWidgetItem(rowItem)
                childItem.setText(0, str(child.tag))
                childItem.setExpanded(True)
                if not child.getchildren():
                    childItem.setText(1, str(child.text))             
                else:
                    self.populate(child, childItem)        


    
class SGETreeView2(QtGui.QTreeWidget):
    def __init__(self, xml=None, entry="host"):
        QtGui.QTreeWidget.__init__(self)
        self.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.setHeaderLabels(['Variable', 'Value'])
        self.data = ElementTree()
        self.data.parse(xml)
        self.entry = entry
        self.root = self.data.findall(self.entry)
        self.populate(self.root)

    def update(self, xml):
        self.data = ElementTree()
        self.data.parse(xml)
        self.root = self.data.find(self.entry)
        #self.rowsRemoved(QModelIndex(), 0, len(self.root))
        self.populate(self.root)        

    def columnCount(self, parent):
        return 2

    def populate(self, data, parent=None):
        forbiden = ('arch_string', 'num_proc', 'load_avg', 
        'mem_total', 'mem_used', 'swap_total','swap_used')
        if not parent:
            parent = self
        # populate the tree with QTreeWidgetItem items
        for row in data:
            if len(row.attrib.keys()): 
                name = row.attrib[row.attrib.keys()[0]]
            else: 
                name = row.tag
            if name not in forbiden:
                rowItem = QtGui.QTreeWidgetItem(parent)
                rowItem.setText(0, str(name))
                rowItem.setText(1,str(row.text))
                rowItem.setExpanded(True)
                if len(row.getchildren()) > 1:
                    self.populate(row, rowItem)



def QChart(parent, type, **kwargs):
    class PyQtChart(type, QtGui.QWidget):
        def __init__(self, parent, **kwargs):
            QtGui.QWidget.__init__(self, parent, **kwargs)
            type.__init__(self, kwargs["size"].width(), kwargs["size"].height())
            self.name = ""
            self.pix = QtGui.QPixmap()
        def download(self):
            file = "/tmp/%s.%f.png" % (self.name, time.time())
            type.download(self, file)
            self.pix.load(file)
        def paintEvent(self, event):
            p = QtGui.QPainter(self)
            p.drawPixmap(0,0,self.pix)
            super(PyQtChart, self).paintEvent(event)
    return PyQtChart(parent, **kwargs)



