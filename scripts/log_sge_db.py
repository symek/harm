#!/usr/bin/python
import sys, socket, time, random
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
from ordereddict import OrderedDict

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

def qacct_to_dict(text, tasks=False, order_list=None):
    """text is an output from qaccet -j command. When tasks=True, 
    it splits info into per task dictionaries. Returns an OrderedDict class."""
    def getValue(value):
        if value.isdigit(): 
            value = int(value)
        else:
            try: 
                value = float(value)
            except: 
                pass
        return value
    def reorder_dict(d, l):
        out = OrderedDict()
        left = []
        for key in l:
            if key in d.keys():
                out[key] = d[key]
        for key in d:
            if key not in out:
                out[key] = d[key]
        return out

    f = text.split(62*"=")
    out = OrderedDict()
    for job in f:
        j = OrderedDict()
        job = job.split("\n")
        for tag in job:
            tag = tag.strip().split()
            if len(tag) > 1:
                j[tag[0]] = getValue(" ".join(tag[1:]))
        if order_list: 
            j = reorder_dict(j, order_list)
        if j.keys():
            if not tasks:
                out[str(j['jobnumber'])] = j
            else:
                out[".".join([str(j['jobnumber']), str(j['taskid'])])] = j
    return out

def read_qacct(job_id, tasks=True):
    """Calls SGE qacct command and returns its output in a format of dictonary,
    in case job_id was correct (at least a single task in the job has been finished.)
    """
    t = os.popen("qacct -j %s" % job_id).read()
    if not t.startswith("error:"):
        return qacct_to_dict(t, tasks)
    return None


def update_database(db, job_id):
        """Update per task entires in database job entry with qacct -j job_id query.
        """
        # Deal with models' indices,
        # TODO: Is this the best place to get unique rows indices?
        print dir(utilities)
        model = utilities.read_qacct(job_id, True)
        # Database doc and relevant sub-entry:
        job   = db[job_id]
        tasks = job["JB_ja_tasks"]['ulong_sublist']
        #FIXME: shouldn't it be opposite (per task in qacct create db task?)
        for task in tasks:
            task_id  = task['JAT_task_number']
            task_str = ".".join([job_id, task_id])
            # Task might not be in qacct yet:
            if not task_str in model:
                continue
            # TODO: by ignoring bellow line, we dismiss *all* render time log data.
            # and copy everything from qacct, which might be better or not...
            if not "JAT_scaled_usage_list" in task: pass
            task['JAT_scaled_usage_list'] = dict()
            task['JAT_scaled_usage_list']['scaled'] = []
            # A list of tasks measurements alligned with 
            # an original qstat format:
            scaled = task["JAT_scaled_usage_list"]['scaled']
            new_scaled = []
            # print model[task_str]
            # Take all but first 10 fields:
            for data in model[task_str].keys():
                _d = OrderedDict()
                _d['UA_name'] = data
                _d['UA_value']= model[task_str][data]
                new_scaled.append(_d)
            # Copy fields:
            task["JAT_scaled_usage_list"]['scaled'] = new_scaled
        job["JB_ja_tasks"]['ulong_sublist'] = tasks
        # Save doc in database:
        db.update([job])
        print "HARM: Last task triggered update: %s in %s" % (str(job_id), os.getenv("CDB_SERVER"))



def main():
    # Our variables
    db    = 'sge_db'
    jobid = sys.argv[1]
    #host  = socket.gethostname()
    server = Server(os.getenv("CDB_SERVER"))
    account=  None #read_qacct(jobid)
    for item in os.environ:
        if item.startswith("SGE_"):
            print item + ": ",
            print os.environ[item]
    print "HARM: Server found."


    # Connect to database
    if db in server:
        db = server[db]
        print "HARM: database connected"
    else:
        db = server.create(db)
        print "HARM: databased created"



    # Safe task specific data in dbt:
    taskid = os.getenv("SGE_TASK_ID", None)
    lastid = os.getenv("SGE_TASK_LAST", None)

    # This is last task from a job, update cdb:
    if taskid == lastid:
        update_database(db, jobid)
        return 0

    # Get data or exit on fail:
    try:
        tree = ElementTree.parse(os.popen(SGE_JOB_DETAILS % jobid))
        _dict  = XmlDictConfig(tree.getroot())['djob_info']['element']
        print "HARM: ETree parsed and converted to dictionary."
    except:
        print "Can't parse Etree or convert its XML to dictonary."
        return 0


    model = Model()
    model._dict = _dict

    # Get job scripts details:
    job_script = os.getenv("JOB_SCRIPT", None)
    if job_script:
        try:
            f = open(job_script)
            job_script_parm = f.read()
            f.close()
        except:
            job_script_parm = None
    else:
        job_script_parm = None


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
    print "HARM: Model prepared."

   


    #We need to make sure, two renders aren't finishing at the same time:
    # FIXME: 
    if not jobid in db:
        time.sleep(random.random()*5)

    # Create new db document in case it's not already there:
    if not jobid in db:
        db[jobid] = dict(model._dict)
        #job       = db[jobid]
        print "HARM: first task, creating document."
    # Or update existing one:
    else:
        job       = db[jobid]
        print "HARM: job retrieved from db."
        # The tricky part is to make sure we are not overwriting per task informations.
        # As much as I wanted to keep this data in raw form so thay conform with qstat output,
        # I can't do this here. Overwise I would have to store per frame information in different place.

        try:    
            cur_tasks = model._dict["JB_ja_tasks"]['ulong_sublist']
            # Make sure we deal with lists of dictionaries, not stright dictionaries. 
            if isinstance(cur_tasks, dict):
                cur_tasks = [cur_tasks]
        except:
            print "No JB_ja_tasks found? Exit."
            return 0
        
        try:
            old_tasks = job["JB_ja_tasks"]['ulong_sublist']
            if isinstance(old_tasks, dict):
                old_tasks = [old_tasks]
            # For every task found in database,
            # check if it was alraedy updated with qaccet, do it if not,
            # then copy it into cur_tasks - unless it's already in.
            for task in old_tasks:
                old_task_id = task['JAT_task_number']
                if old_task_id not in [ct['JAT_task_number'] for ct in cur_tasks]:
                    cur_tasks.append(task)  
        except: 
            pass


        # Finally copy all details into job structure:
        print "HARM: copying keys to model."
        for key in model._dict:
            job[key] = model._dict[key]
        # Also copy combined tasks into job:    
        job["JB_ja_tasks"]['ulong_sublist'] = cur_tasks
        # Safe also a content of job_script:
        job['JOB_SCRIPT'] = job_script_parm
        # Save job in database:
        print "HARM: About to save job document to db."
        #db[jobid] = job # This freezes our process randomly (it stops and hangs in mem forever)
        db.update([job])
        print "HARM: Job %s logged in %s" % (str(jobid), os.getenv("CDB_SERVER"))

    # Finally return 0;
    return 0

if __name__ == "__main__": main()


