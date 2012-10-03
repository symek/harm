from PyQt4.QtCore import *
import tokens
import os

##########################################################
# Xml****Config are work-horses in custom Qt models      #
##########################################################

## {{{ http://code.activestate.com/recipes/410469/ (r5)
from xml.etree import ElementTree

class XmlListConfig(list):
    def __init__(self, aList):
        for element in aList:
            if element:
                # treat like dict
                if len(element) == 1 or element[0].tag != element[1].tag:
                    self.append(XmlDictConfig(element))
                # treat like list
                elif element[0].tag == element[1].tag:
                    self.append(XmlListConfig(element))
            elif element.text:
                text = element.text.strip()
                if text:
                    self.append(text)


class XmlDictConfig(dict):
    '''
    Example usage:

    >>> tree = ElementTree.parse('your_file.xml')
    >>> root = tree.getroot()
    >>> xmldict = XmlDictConfig(root)

    Or, if you want to use an XML string:

    >>> root = ElementTree.XML(xml_string)
    >>> xmldict = XmlDictConfig(root)

    And then use xmldict for what it is... a dict.
    '''
    def __init__(self, parent_element):
        if parent_element.items():
            self.update(dict(parent_element.items()))
        for element in parent_element:
            if element:
                # treat like dict - we assume that if the first two tags
                # in a series are different, then they are all different.
                if len(element) == 1 or element[0].tag != element[1].tag:
                    aDict = XmlDictConfig(element)
                # treat like list - we assume that if the first two tags
                # in a series are the same, then the rest are the same.
                else:
                    # here, we put the list in dictionary; the key is the
                    # tag name the list elements all share in common, and
                    # the value is the list itself 
                    aDict = {element[0].tag: XmlListConfig(element)}
                # if the tag has attributes, add those to the dict
                if element.items():
                    aDict.update(dict(element.items()))
                self.update({element.tag: aDict})
            # this assumes that if you've got an attribute in a tag,
            # you won't be having any text. This may or may not be a 
            # good idea -- time will tell. It works for the way we are
            # currently doing XML configuration files...
            elif element.items():
                self.update({element.tag: dict(element.items())})
            # finally, if there are no child tags and no attributes, extract
            # the text
            else:
                self.update({element.tag: element.text})
## end of http://code.activestate.com/recipes/410469/ }}}



#################################################################
#               Sge Abstract (base) Model                       #   
# ###############################################################

class SgeTableModelBase():
    def __init__(self):
        '''_tree is an ElementTree as parsed stright from a XML.
           _xml is stripped version of a tree in dict() format.
           _data is list of the lists version of item in _xml.
           _head is a dict of headers found in xml items.'''
        self._tree = None
        self._dict  = {}
        self._data = []
        self._head = {}

    def flags(self, index):
        flag = super(self.__class__, self).flags(index)
        return flag | Qt.ItemIsEditable

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        if len(self._data):
            return len(self._data[-1])
        return 0

    def _tag2idx(self, item):
        '''This builds self._head dict {1:header, 2:another, ...}'''
        _map = {}
        for x in range(len(item.keys())):
            _map[x] = item.keys()[x]
        return _map

    def data_hooks(self, index, value):
        '''Loops through all hook_* function of self, and executes it
           to preprocess data of a model. Hooks to be provided by derived classes'''
        for func in dir(self):
            if func.startswith("hook"):
                value = self.__getattribute__(func)(index, value)

        # Process data types: 
        if not value: 
            return None 
        if value.isdigit(): 
            value = int(value)
        try: 
            value = float(value)
        except: 
            pass
        return value
              
    def data(self, index, role):
        ''''Data access.'''
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()

        # Read element from a elementTree sub-entry :
        value = self._data[index.row()][index.column()]
        value = self.data_hooks(index, value)
        if not value: return QVariant()        
        # Finally return something meaningfull:
        return QVariant(value)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        '''Headers builder. Note crude tokens replacement.'''
        # Replaces columns/rows names view custom tokens;
        def header_replace(name):
            if name in tokens.header.keys():
                name = tokens.header[name]
            return name
        # Nothing to do here:
        if role != Qt.DisplayRole:
            return QVariant()
        # Horizontal headers:
        if orientation == Qt.Horizontal and len(self._data):
            return QVariant(header_replace(self._head[section]))
        # Vertical headers:
        elif orientation == Qt.Vertical and len(self._data):
            return QVariant(header_replace(int(section+1)))
        return QVariant()

    def parse_time_string(self, time):
        '''Parses the time string to reasonable format.'''
        date, time = time.split("T")
        return " ".join((time, date))




#################################################################
#               Job Table Model                              #   
# ###############################################################

class JobsModel(QAbstractTableModel, SgeTableModelBase):
    def __init__(self,  parent=None, *args):
        super(self.__class__, self).__init__()
      
    def update(self, sge_command, token='job_info', sort_by_field=7, reverse=True):
        '''Main function of derived model. Builds _data list from input.'''
        from operator import itemgetter
        # All dirty data. We need to duplicate it here,
        # to keep things clean down the stream.
        self._tree = ElementTree.parse(os.popen(sge_command))
        self._dict  = XmlDictConfig(self._tree.getroot())[token]
        self._data = []

        # XmlDictConfig returns string instead of dict in case *_info are empty! Grrr...!
        if isinstance(self._dict, {}.__class__):
            d = self._dict['job_list']
            self._data += [[x[key] for key in x.keys()] for x in d]
            self._data = sorted(self._data,  key=itemgetter(sort_by_field))
            if reverse:
                self._data.reverse()
            self._head = self._tag2idx(d[-1])
    
    def hook_timestring(self, index, value):
        # Change time string formating:
        if self._head[index.column()] in tokens.time_strings: 
            value = self.parse_time_string(value)
        return value

    def hook_machinename(self, index, value):
        # Shorten machine name in Tasks view:
        if self._head[index.column()] == 'queue_name':
            if value: 
                value = value.split("@")[-1]
                if "." in value:
                    value = value.split(".")[0]
        return value




def main():
    import os
    tree = ElementTree.parse(os.popen('qstat -xml -u "*"'))
    root = tree.getroot()
    d    = XmlDictConfig(root)
    d    = JobsModel()
    d.update('qstat -xml -u "*"')
    print d.rowCount(None)
    print d.data(QModelIndex(0,2))



if __name__ == '__main__': main()

