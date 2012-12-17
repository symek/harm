#!/usr/bin/python
import sys, socket
# Softimage polutes PYTHONPATH, we need to revert sys.path to system defaults:
# FIXME: Don't hard code it here.
if True in ['softimage' in path for path in sys.path]:
    sys.path = [ '/STUDIO/studio-packages', '/usr/lib64/python26.zip',
                 '/usr/lib64/python2.6', '/usr/lib64/python2.6/plat-linux2', 
                 '/usr/lib64/python2.6/lib-tk', '/usr/lib64/python2.6/lib-old', 
                 '/usr/lib64/python2.6/lib-dynload', '/usr/lib64/python2.6/site-packages', 
                 '/usr/lib64/python2.6/site-packages/gst-0.10', '/usr/lib64/python2.6/site-packages/gtk-2.0', 
                 '/usr/lib64/python2.6/site-packages/webkit-1.0', '/usr/lib/python2.6/site-packages',
                 "/STUDIO/scripts/harm-sge-db/src"]

#Now the rest should work as usual:
sys.path.append("/STUDIO/scripts/harm-sge-db/src")
import os
from couchdb import Server
from constants import *
import utilities
from xml.etree import ElementTree

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

#  http://stackoverflow.com/questions/9807634/find-all-occurences-of-a-key-in-nested-python-dictionaries-and-lists
def find(key, value):
    for k, v in value.iteritems():
        if k == key:
            yield v
        elif isinstance(v, dict):
            for result in find(key, v):
                yield result
        elif isinstance(v, list):
            for d in v:
                if isinstance(d, dict):
                    for result in find(key, d):
                        yield result
                for result in find(key, d):
                    yield result


class Model:
    pass

# Our variables
db    = 'sge_db'
jobid = sys.argv[1]
taskid= sys.argv[-1]
host  = socket.gethostname()
server = Server(os.getenv("CDB_SERVER"))

# Connect to database
if db in server:
    db = server[db]
else:
    db = server.create(db)


# Get data or exit on fail:
try:
    tree = ElementTree.parse(os.popen(SGE_JOB_DETAILS % jobid))
    _dict  = XmlDictConfig(tree.getroot())['djob_info']['element']
except:
    sys.exit()


model = Model()
model._dict = _dict

# Process fields to remove unlegal character:
for key in model._dict:
    if key.startswith("__"):
        nkey  = key[2:]
    elif key.startswith("_"):
        nkey = key[1:]
    else:
        continue
    value = model._dict.pop(key)
    model._dict[nkey] = value

# Create new db document in case it's not already there:
if not jobid in db:
    db[jobid] = dict(model._dict)
    job       = db[jobid]
# Or update existing one:
else:
    job       = db[jobid]
    # The tricky part is to make sure we are not overwriting per task informations.
    # As much as I wanted to keep this data in raw form so thay conform with qstat output,
    # I can't do this here. Overwise I would have to store per frame information in different place.
    old_tasks = job["JB_ja_tasks"]['ulong_sublist']
    cur_tasks = model._dict["JB_ja_tasks"]['ulong_sublist']

    # Make sure we deal with lists of dictionaries, not stright dictionaries. 
    if isinstance(cur_tasks, dict):
        cur_tasks = [cur_tasks]
    if isinstance(old_tasks, dict):
        old_tasks = [old_tasks]

    #print old_tasks
    #print cur_tasks
    # For every task in old job
    for task in old_tasks:
        old_task_id = task['JAT_task_number']
        if old_task_id not in [t['JAT_task_number'] for t in cur_tasks]:
            cur_tasks.append(task)
    for task in cur_tasks:
        if task['JAT_task_number'] == taskid:
            #print "JAT TASK NUMBER" + task['JAT_task_number']
            #print "TASK ID" + taskid
            task['host_name'] = host
            #print "HOSTNAME: " + task['host_name']
    for key in model._dict:
        job[key] = model._dict[key]
    # Copy combined tasks into job:    
    job["JB_ja_tasks"]['ulong_sublist'] = cur_tasks
    # Save job in database:
    db[jobid] = job


