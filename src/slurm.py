import subprocess
# Python 2.6 compatibility:
try:
    from collections import OrderedDict, defaultdict
except ImportError:
    from ordereddict import OrderedDict


# Slurm commands:
SLURM_JOBS_GROUPED_CMD = 'squeue -t <STATES/> -o "%F %P %u %T %j %V %e %M %K %A"'

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



def parse_slurm_output(output, length=None, reverse_order=True):
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
    head = [word.strip() for word in head.split()]
    lines = [line.split() for line in lines if line]
    return lines, head


def collapse_list_by_field(data, header, identity_field="ARRAY_JOB_ID",\
                           collapse_fields=('ARRAY_TASK_ID',), reverse_order=False):
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

    

def get_slurm_output(command, max_lines, reverse_order):
    """ Performs basic parsing of squeu output.
    """
    data, header = (None, None)

    try:
        out, err = subprocess.Popen(command, shell=True, \
        stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
        if out:
            data, head = parse_slurm_output(out, max_lines, reverse_order)
            header     = OrderedDict()
            for item in head:
                header[head.index(item)] = item
    except: 
        print "Counld't get Slurm output."
        print err
    return data, header



def get_pending_jobs(max_jobs=150, reverse_order=True):
    """ Get a list of pending jobs from slurm.
    """
    command      = SLURM_JOBS_GROUPED_CMD.replace("<STATES/>", "PD")
    data, header = get_slurm_output(command, max_jobs, reverse_order)
    if data:
        return data, header
    return  


def get_notpending_jobs(max_jobs=None, reverse_order=True):
    """
    """
    command      = SLURM_JOBS_GROUPED_CMD.replace("<STATES/>", "CD,CA,F,S,ST,NF,R,PR")
    data, header = get_slurm_output(command, max_jobs, reverse_order)
    if data:
        data, _dict = collapse_list_by_field(data, header)
        return data, header
    return  

    