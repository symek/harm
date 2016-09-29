import subprocess
# Python 2.6 compatibility:
try:
    from collections import OrderedDict, defaultdict
except ImportError:
    from ordereddict import OrderedDict


# Slurm commands:
SLURM_JOBS_GROUPED_CMD = 'squeue -t <STATES/> -o "%F %P %u %T %j %V %e %M %K %A"'
SLURM_JOB_DETAILS      = 'scontrol show job <JOBID/>_<TASKID/>'
SLURM_JOBS_HISTORY_ALL = 'sacct -u <USER/> -o "JobId,Partition,User,State,JobName,Submit,Start,End,ExitCode" -P'
SLURM_JOB_HISTORY_DETAIL = 'sacct -j <JOBID/> -o "All" -P'
SLURM_CLUSTER_LIST       = 'scontrol show nodes'

# TODO: Remove and import hafarm utils upon merge.
def collapse_digits_to_sequence(frames):
    ''' Given frames is a list/tuple of digits [1,2,4],  
        collapse it into [(1,2), (4,..) ...]
    '''
    frames = sorted(list(frames))
    frames = [int(x) for x in frames]
    sequence = [] 
    start = True

    for f in frames:
        if start: 
            part = [f,f]
            sequence += [part]
            start   = False
            continue
        if (f - 1) == frames[frames.index(f)-1]:
            part[1] = f
            continue
        else:
            part  = [f,f]
            sequence += [part]

    sequence = [tuple(x) for x in sequence]
    return sequence



def parse_slurm_output_to_dict(output):
    """ Post process stdout finding key=value items.
    """
    def parse_task(output):
        out = output.split()
        data   = []
        header = []
        dict_  = OrderedDict()
        for item in out:
            var = item.split("=")
            name, var = var[0], ",".join(var[1:])
            data   += [(name,var)]
            header += [name.strip()]
            dict_[name] = var
        return data, header, dict_

    output = output.split("\n\n")
    data   = []
    for task in output:
        l, h, d = parse_task(task)
        if not d or not h:
            continue
        header = h
        data   += [d]
    return data, header

        

def parse_slurm_output_to_list(output, length=None, reverse_order=True, split_char=None):
    """ Post process stdout from an application spliting it into lines
        and lines lines into words. Assummies first line is a header.
    """
    lines = output.split("\n")
    if len(lines) == 1: 
        lines  += [""]

    head, lines = lines[0], lines[1:]
    if reverse_order:
        lines.reverse()

    if length:
        assert isinstance(length, int)
        lines = lines[:max(length, 1)]
    head = [word.strip() for word in head.split(split_char)]
    lines = [line.split(split_char) for line in lines if line]
    return lines, head


def collapse_list_by_field(data, header, identity_field="ARRAY_JOB_ID", 
                          collapse_fields=('ARRAY_TASK_ID',), 
                          reverse_order=False):
    """ Collapses series of lists based on shared identity_key field,
        and optionally collapses other fields.
    """
    _dict       = OrderedDict()
    key_idx     = header.values().index(identity_field)
    taskid_idx  = header.values().index('ARRAY_TASK_ID')
    fields_idxs = [header.values().index(key) for key in collapse_fields]

    for line in data:
        ident = line[key_idx]
        if ident not in _dict:
            _dict[ident] = line
        else:
            for idx in fields_idxs:
                _dict[ident][idx] = ",".join([_dict[ident][idx], line[idx]])

    for key in _dict:
        frames = _dict[key][taskid_idx]
        frames = frames.split(",")
        areframes = [x.isdigit() for x in frames]
        if False in areframes: 
            continue
        frames = [int(x) for x in frames]
        frames.sort()
        # frames = collapse_digits_to_sequence(frames)
        _dict[key][taskid_idx] = "%s...%s" % (str(frames[0]), str(frames[-1]))

    return _dict.values(), _dict

    

def get_std_output(command):
    """ Performs basic parsing of squeu output.
    """
    out, err = (None, None)
    #TODO: We need proper logging facility. 
    try:
        out, err = subprocess.Popen(command, shell=True, \
        stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    except: 
        print "Counld't get output from: %s" % command # TODO: LOGGER
        print err
    return out, err



def get_pending_jobs(max_jobs=300, reverse_order=True):
    """ Get a list of pending jobs from slurm.
    """
    command   = SLURM_JOBS_GROUPED_CMD.replace("<STATES/>", "PD")
    data, err = get_std_output(command)
    if data:
        data, head = parse_slurm_output_to_list(data, max_jobs, reverse_order)
        header     = OrderedDict()
        for item in head:
            header[head.index(item)] = item
        return data, header
    return  


def get_notpending_jobs(max_jobs=None, reverse_order=True):
    """
    """
    command   = SLURM_JOBS_GROUPED_CMD.replace("<STATES/>", "CD,CA,F,S,ST,NF,R,PR")
    data, err = get_std_output(command)
    if data:
        data, head = parse_slurm_output_to_list(data, max_jobs, reverse_order)
        header     = OrderedDict()
        for item in head:
            header[head.index(item)] = item
        data, _dict  = collapse_list_by_field(data, header)
        return data, header
    return  

def get_current_jobs(max_jobs=300, reverse_order=True):
    """ Only pending and rendering
    """
    command   = SLURM_JOBS_GROUPED_CMD.replace("<STATES/>", "PD,R")
    data, err = get_std_output(command)
    if data:
        data, head = parse_slurm_output_to_list(data, max_jobs, reverse_order)
        header     = OrderedDict()
        for item in head:
            header[head.index(item)] = item
        data, _dict  = collapse_list_by_field(data, header)
        return data, header
    return 

def get_accounted_jobs(user, jobid=None, reverse_order=True):
    """ Only pending and rendering
    """
    from os import getlogin
    if user == "":
        user = getlogin()

    command   = SLURM_JOBS_HISTORY_ALL.replace("<USER/>", "%s" % user)
    if jobid:
        command += " -j %s" % jobid
    data, err = get_std_output(command)
    if data:
        data, head = parse_slurm_output_to_list(data, 500, reverse_order, "|")
        header     = OrderedDict()
        for item in head:
            header[head.index(item)] = item
        return data, header
    return 

def get_accounted_job_details(jobid=None, reverse_order=True):
    """ Only pending and rendering
    """

    command   = SLURM_JOB_HISTORY_DETAIL.replace("<JOBID/>", "%s" % jobid)
   
    data, err = get_std_output(command)
    if data:
        data, head = parse_slurm_output_to_list(data, 500, reverse_order, "|")
        header     = OrderedDict()
        for item in head:
            header[head.index(item)] = item
        return data, header
    return 


def get_nodes_info(node=None, reverse_order=False):
    """ Get details about nodes states from scontrol show node command.
        Terribly unpleasent due to varying keys and syntax.
    """
    def parse_scontrolShowNode_output(output):
            nodes = output.split("\n\n")
            data   = []
            header = []
            dict_  = OrderedDict()
            hostname= ""
            build_header = True

            for node in nodes:
                preItems = node.split("\n") #node.split()[:-1]
                items = []
                for item in preItems:
                    if len(item.split("=")) > 2:
                        item = item.split()
                        items += item
                    else:
                        items.append(item)
                line = []
                d_   = OrderedDict()
                for item in items:
                    var = item.split("=")
                    name, var = var[0], item[len(var[0])+1:]
                    if name == 'NodeName':
                        hostname = var
                    line += [var]
                    if build_header:
                        header += [name.strip()]
                    d_[name] = var

                data.append(line)
                dict_[hostname] = d_
                build_header = False

            return data, header, dict_

    def dict_to_list(_dict):
        """ Create a list of lists from series of similar dictionaries, 
            taking care of missing keys in some of them.
        """
        header = []
        data   = []
        # fill header
        for nodeid in _dict.keys():
            node = _dict[nodeid]
            for head in node.keys():
                if head not in header:
                    header.append(head)
        # gather data
        for nodeid in _dict.keys():
            node = _dict[nodeid]
            line = []
            for head in header:
                if head not in node.keys():
                    line.append("N/A")
                else:
                    value = node[head]
                    line.append(value)
            if line[0] != "N/A":
                data.append(line)

        return data, header


    data, err = get_std_output(SLURM_CLUSTER_LIST)
    if data:
        data, head, _dict = parse_scontrolShowNode_output(data)
        data, head = dict_to_list(_dict)
        header     = OrderedDict()
        for item in head:
            header[head.index(item)] = item
        return data, header
    return  


def get_job_stats(jobid, taskid=""):
    """ As names implies.
    """
    command = SLURM_JOB_DETAILS.replace("<JOBID/>", str(jobid))
    command = command.replace("<TASKID/>", str(taskid))
    # remove trailing underscore for non-tasks specification.
    if not taskid:
        command = command[:-1]
    data, err = get_std_output(command)

    if data:
        data, header = parse_slurm_output_to_dict(data)
        return data, header
    return None, None

def convert_seconds_to_HMS(seconds):
    ''' Converts seconds to a time string HH:MM:SS
    '''
    hours = seconds // 3600.0
    seconds -= 3600.0*hours
    minutes = seconds // 60.0
    seconds -= 60.0*minutes
    return "%02d:%02d:%02d" % (hours, minutes, seconds)

def convert_strtime_to_seconds(time_string):
    '''Converts time in asc format to seconds'''
    from time import strptime, mktime
    format = '%H:%M:%S'
    time  = time_string.split(":")
    time  = [int(x) for x in time]
    hours, minutes, seconds = time
    return hours*3600+minutes*60+seconds

def render_job_stats_to_text(jobid):
  
    stats, header = get_job_stats(jobid)

    runtime    = []
    completed  = []
    failed     = []
    pending    = []
    inprogress = []
    eta        = []

    if not stats:
        return ""

    for task in stats:
        if task['JobState'] in ('COMPLETED', "RUNNING"):
            runtime   += [task['RunTime']]
        if task['JobState'] == 'COMPLETED':
            completed += [task['ArrayTaskId']]
        elif task['JobState'] == 'FAILED':
            failed    += [task['ArrayTaskId']] 
        elif task['JobState'] == 'PENDING':
            pending   += [task['ArrayTaskId']]
        elif task['JobState'] == 'RUNNING':
            inprogress += [task['ArrayTaskId']]


    render_avg = sum([convert_strtime_to_seconds(x) for x in runtime]) / max(len(runtime),1) * 1.0

    if not runtime: 
        runtime.append(0.0)

    
    text  = ""
    text += "                 MIN            MAX            AVG    \n" 
    text += "==========================================================\n"
    text += " CPU:        %s         %s        %s         \n" % (runtime[0], runtime[-1], convert_seconds_to_HMS(render_avg))
    
    text += "\n"
    text += "Frames completed: %s\n" % ",".join(completed)
    text += "Frames pending  : %s\n" % ",".join(pending)
    text += "Frames failed   : %s\n" % ",".join(failed)
    text += "Currently render: %s\n" % ','.join(inprogress)
    text += "Estimated finish: %s\n" %  convert_seconds_to_HMS(render_avg*len(pending) / max(len(inprogress),1.0)*1.0)  #% str(getInHMS(details['eta'] / 10.0 / len(details['current_render'] ))) + " (avarage_time * pending_frames / activemachines )"

    return text


if __name__ == "__main__": 
    import sys
    render_job_stats_to_text(sys.argv[-1])