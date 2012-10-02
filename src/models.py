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
#               Job Table Model                              #   
# ###############################################################

class JobsModel(QAbstractTableModel):
    def __init__(self,  parent=None, *args):
        super(JobsModel, self).__init__()
        self._data = {}
      
    def update(self, token='qstat -xml -u "*"'):
        from operator import itemgetter
        tree  = ElementTree.parse(os.popen(token))
        root  = tree.getroot()
        self._dict = XmlDictConfig(root)
        self._data = []
        if self.has_items(self._dict)[0]:
            d = self._dict['job_info']['job_list']
            self._data += [[x[key] for key in x.keys()] for x in d]
            self._data = sorted(self._data,  key=itemgetter(7))
            self._data.reverse()
            print self._data
           
    def flags(self, index):
        flag = super(JobsModel, self).flags(index)
        return flag | Qt.ItemIsEditable

    def has_items(self, d):
        # XmlDictConfig returns string instead of dict in case *_info are empty! Grrr...!
        # At least one case should return True (job_info or queue_info are dicts
        # i.e. they are not empty):
        return [isinstance(d[x], {}.__class__) for x in ('job_info', 'queue_info')]

    def rowCount(self, parent):
        # Row count is a sum of both entires (if they exist):
        return len(self._data)

    def columnCount(self, parent):
        if len(self._data):
            return len(self._data[-1])
        return 0

    def _tag2idx(self, item):
        _map = {}
        for x in range(len(item.keys())):
            _map[x] = item.keys()[x]
        return _map

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()

        # Read element from a elementTree sub-entry :
        tagidx = self._tag2idx(self._dict['job_info']['job_list'][-1])
        value  = self._data[index.row()][index.column()]

        # Change time string formating:
        if tagidx[index.column()] in tokens.time_strings: 
            value = self.parse_time_string(value)

        # Shorten machine name in Tasks view:
        if tagidx[index.column()] == 'queue_name':
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
        # Replaces columns/rows names view custom tokens;
        def header_replace(name):
            if name in tokens.header.keys():
                name = tokens.header[name]
            return name

        # Nothing to do here:
        if role != Qt.DisplayRole:
            return QVariant()
    
        # Shortcut:
        if len(self._data):
            tagidx = self._tag2idx(self._dict['job_info']['job_list'][-1])

        if orientation == Qt.Horizontal:
            # tagidx keeps track of column names (dict.key()):
            if self.has_items(self._dict):
                return QVariant(header_replace(tagidx[section]))

        elif orientation == Qt.Vertical:
            if self.has_items(self._dict):
                return QVariant(header_replace(int(section+1)))

        return QVariant()

    def parse_time_string(self, time):
        date, time = time.split("T")
        return " ".join((time, date))



def main():
    import os
    tree = ElementTree.parse(os.popen('qstat -xml -u "*"'))
    root = tree.getroot()
    d    = XmlDictConfig(root)
    d    = JobsModel()
    d.update()
    print d.rowCount(None)
    print d.data(0,2)



if __name__ == '__main__': main()

