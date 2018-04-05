import os, sys
from ordereddict import OrderedDict

REZ_FOUND = False

if not os.getenv("REZ_CONFIG_FILE", None):
    try:
        import rez 
        REZ_FOUND = True
    except ImportError, e:
       pass
else:
    from glob import glob
    rez_path = os.environ['REZ_CONFIG_FILE']
    rez_path = os.path.dirname(rez_path)
    rez_candidate = os.path.join(rez_path, "lib64/python2.7/site-packages/rez-*.egg")
    rez_candidate = glob(rez_candidate)
    if rez_candidate:
        sys.path.append(rez_candidate[0])
        import rez 
        REZ_FOUND = True

def run_rez_shell(command, rez_pkg, weight=False):
        """Runs provided command inside rez-resolved shell.

            Args: 
                command (str): custom command
            Returns:
                pid: Process object of subshell.

            Note: pid runs in separate process and needs to be waited with wait()
                command outside this function, if commad takes time.
        """
        if not REZ_FOUND:
            print "Can't execute command in rez configured subshell." 
            print "No rez package found! (does $REZ_CONFIG_FILE exist?) "
            return False

        from rez.resolved_context import ResolvedContext

        if not command:
            return self.EmtyProcess()

        context = ResolvedContext(rez_pkg)
        rez_pid = context.execute_command(command)  

        return rez_pid 

# FIXME: TO BE REMOVED!
def findIcons(path=None):
    icons = {}
    if not path:
        path = "/STUDIO/scripts/harm/icons"
    files = os.listdir(path)
    for file in files:
        if os.path.isfile(os.path.join(path, file)):
            p, f  = os.path.split(file)
            f, ext = os.path.splitext(f)
            icons[f] = os.path.join(path, file)
    return icons

def expand_pattern(pattern):
    '''Expands patterns like "1,2,3-10:1,11,12" into a list of frames (of strings)'''
    frames = []
    subpatterns = pattern.split(",")
    for item in subpatterns:
        if "-" in item:
            item = item.split(":")[0]
            start, end = item.split("-")
            for x in range(int(start), int(end)+1):
                frames.append(str(x))
        elif not "-" in item and item.isdigit():
            frames.append(item)
    return frames


def tag2idx(model, attrib=False, attrib_num=0):
    '''Builds a dynamic map integer:tag keys of column's names.'''
    index_map = {}
    if len(model):
        for index in range(len(model)):
            if attrib: 
                attr = model[index].attrib.keys()[attrib_num]
                name = model[index].attrib[attr]
            else: 
                name = model[index].tag
            index_map[name] = index
        return index_map

def to_number(x):
    """Extract digits from a string. Always returns a digits, on error
    it returns 0.0!
    """
    import re
    x = re.sub(r'[^\d\.]', '', str(x)).strip()
    try:
        x = float(x)
    except:
        x = int(x)
    if x:
        return x
    return 0.0

def clamp(value, _min, _max):
    """Clamps value between min and max values."""
    if value > _max: return _max
    if value < _min: return _min
    return value
        
        
def fit(x, a, b, c, d):
    """Fits x between 'a' and 'b' based on 'c' and 'd' distance."""
    return c+((x-a)/(b-a))*(d-c)


def epoc_to_str_time(t, sge_time_format = "%Y-%m-%dT%H:%M:%S"):
    """Epoc to sge time string convertion."""
    import time
    data = time.strftime(sge_time_format, time.gmtime(float(t)))
    return data #"".join(data.split()[3:])
        
def string_to_elapsed_time(value):
    """Returns time difference provided SGE specific string time."""
    import time, datetime
    sge_time_format = "%Y-%m-%dT%H:%M:%S"
    try:
        started = time.mktime(time.strptime(value, sge_time_format))
        now     = time.time()
        elapsed = int(now - started)
        value   = str(datetime.timedelta(seconds=elapsed))
    except:
        pass
    return value


#http://stackoverflow.com/questions/842059/is-there-a-portable-way-to-get-the-current-username-in-python
def get_username():
    '''Cross-platform method to get to the user name.'''
    import getpass
    return getpass.getuser()

def render_basic_job_info(data):
    '''Renders basic job information from job detail model.'''
    def safe_key(key, data):
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
        if len(list(find(key, data))) > 0:
            return list(find(key, data))[0]
        else:
            names = list(find("VA_variable", data))
            value = list(find("VA_value", data))
            if key in names and len(names) == len(value):
                index = names.index(key)
                return value[index]
        return None


    import time
    text = """
    SGE job number : %s 
    Tasks completed: %s (or in progress)
    Tasks range    : %s-%s: %s
    Job owner : %s
    Group     : %s
    Submitted : %s
    Hostname  : %s
    Jobname   : %s
    --------------------------------------
    Procslots : %s
    $JOB      : %s
    $PWD      : %s
    Cluster   : %s
    Output    : %s 
    --------------------------------------
   
    PACKAGES  : %s

    --------------------------------------
    """ % \
    (safe_key('JB_job_number', data), safe_key('JAT_task_number', data), safe_key("RN_min", data), 
           safe_key("RN_max", data), safe_key("RN_step", data),  safe_key('JB_owner', data), safe_key('JB_group', data), 
          time.ctime(int(safe_key('JB_submission_time', data))), safe_key('MR_host', data), 
          safe_key('JB_job_name', data), safe_key('CE_stringval', data),  safe_key('JOB', data), 
          safe_key('PWD', data), safe_key('QR_name', data) , safe_key('OUTPUT_PICTURE',data), safe_key("NEED_LOADED_PACKAGE", data))
    return text

def render_basic_task_info(data):
    str_frame = "\n\n     Frames: (%s)\n\n" % ", ".join([f[1] for f in data])
    for frame in data:
        info = ""
        if not frame[2]:
            str_frame += "    frame %s: No data.\n" % frame[1]
            continue
        for item in frame[2]:
            info += "     %s: %s\n" % item
        str_frame += "     frame %s: \n%s\n" % (frame[1], info)
        str_frame += "--------------------------------------\n"
    return str_frame


def read_rtime(job_id):
    result = os.popen("/STUDIO/scripts/rtime/rtime -f -j %s" % job_id).read()
    return result

def padding(file, format=None, _frame=None):
    """ Recognizes padding convention of a file.
        format: one of: nuke, houdini, shell
        Returns: (host_specific_name, frame number, length, extension).
        """
    import re
    _formats = {'nuke': '%0#d', 'houdini': '$F#', 'shell':'*'}
    frame, length, = None, None
    base, ext = os.path.splitext(file)
    if not base[-1].isdigit(): 
        return (os.path.splitext(file)[0], 0, 0, os.path.splitext(file)[1])
    l = re.split('(\d+)', file)
    if l[-2].isdigit(): (frame, length)  = (int(l[-2]), len(l[-2]))
    if format in _formats.keys():
        format = _formats[format].replace("#",str(length))
        return "".join(l[:-2])+ format + ext, frame, length, ext
    if _frame:
        return "".join(l[:-2]) + str(_frame).zfill(length) + ext, frame, length, ext
    return "".join(l[:-2]), frame, length, ext

# #####################################################
#  Input text is an output from qccet SGE utility     #
########################################################

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
            # if not tasks:
            #     out[str(j['jobnumber'])] = j
            # else:
            out[".".join([str(j['jobnumber']), str(j['taskid'])])] = j
    return out


def read_qacct(job_id, task=0):
    """Calls SGE qacct command and returns its output in a format of dictonary,
    in case job_id was correct (at least a single task in the job has been finished.)
    """
    if task != 0:
        t = os.popen('qacct -j %s -t %s' % (job_id, task)).read()
    else:
        t = os.popen("qacct -j %s" % job_id).read()

    if not t.startswith("error:"):
        return qacct_to_dict(t, task)
    return None


def rotate_nested_dict(d, key):
    """Given a dictionary of dictionarties, it builds a new one with keys 
    taken from children's values.
    """
    output = OrderedDict()#{}
    for item in d:
        if key in d[item]:
            if d[item][key] not in output.keys():
                output[d[item][key]] = [d[item]]
            else:
                output[d[item][key]].append(d[item])
    return output


def install_harm_view(design, view, map_fun=None, db_server=None, db_name="sge_db"):
    """Installs Harm's permanent views in couchdb server. Creates database if needed.
    Views are stored currently on constants module in HarmView class.
    """
    import couchdb
    import couchdb.design
    from constants import harm_views # <-- These are our map functions dictionary
    # TODO: This is another place for replecement with Config() class.
    # The server first:
    if not db_server or not isinstance(db_server, couchdb.Server):
        db_server = couchdb.Server(os.getenv("CDB_SERVER"))
    # The database next:
    if db_name in db_server:
        db = db_server[db_name]
    else:
        # Couchdb doesn't accept just any database name:
        try:
            db_server.create(db_name)
            db = server[db_name]
        except:
            raise Exception, "Can't create a database with specified name %s" % db_name
            return False
    assert db_name in db_server, "No %s in %s" %(db_name, server)

    # Assign provided map_fun, or find it internally (in constants.harm_views)
    if not map_fun:
        if not view in harm_views:
            # Quit in case view name wasn't found:
            print  "Can't find %s in constants.harm_views" % view
            return
        else:
            map_fun = harm_views[view]

    # Creata design document as save it db:
    view = couchdb.design.ViewDefinition(design, view, map_fun)
    view.sync(db)

    # Design doc is there:
    if view.get_doc(db):
        return True
    return



def get_rawpixels_from_file(filename, scale_image=1):
    """ Using OpenImageIO get raw pixels from an image file
        for previewing purposes (uint8).
    """
    import math
    # TODO: Migrate it outside callbacks.py
    try:
        import OpenImageIO as oiio 
    except:
        print "Cant' find OpenImageIO."
        return None, None, None

    source = oiio.ImageBuf(str(filename))

    if not source:
        return None, None, None

    # OIIO to get raw uint pixels rgb
    w = int(math.ceil(source.oriented_width*scale_image))
    h = int(math.ceil(source.oriented_height*scale_image))
    dest = oiio.ImageBuf(oiio.ImageSpec(w, h, 3, oiio.UINT8))

    # DeLinearize optionally 
    if source.spec().format in (oiio.TypeDesc(oiio.HALF), oiio.TypeDesc(oiio.FLOAT)):
        oiio.ImageBufAlgo.colorconvert(source, source, "linear", "sRGB")

    dest.copy(source, oiio.UINT8)
    roi    = oiio.ROI(0, w, 0, h, 0, 1, 0, 3)
    pixels = dest.get_pixels(oiio.UINT8, roi)

    return pixels, w, h


def get_stats_from_image(filename):
    import math
    # TODO: Migrate it outside callbacks.py
    try:
        import OpenImageIO as oiio 
    except:
        print "Cant' find OpenImageIO."
        return None

    source = oiio.ImageInput.open(str(filename))

    if not source:
        print oiio.geterror()
        return

    spec = source.spec()
    info = []

    info.append(["resolution", (spec.width, spec.height, spec.x, spec.y)])
    info.append(["channels: ", spec.channelnames])
    info.append(["format", str(spec.format)])
    if spec.channelformats :
        info.append(["channelformats", str(spec.channelformats)])
    info.append(["alpha channel", str(spec.alpha_channel)])
    info.append(["z channel",  str(spec.z_channel)])
    info.append(["deep", str(spec.deep)])
    for i in range(len(spec.extra_attribs)):
        if type(spec.extra_attribs[i].value) == str:
            info.append([spec.extra_attribs[i].name,  spec.extra_attribs[i].value])
        else:
            info.append([spec.extra_attribs[i].name, spec.extra_attribs[i].value])

    source.close ()

    return info


# http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python/377028
def which(program):
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    def ext_candidates(fpath):
        yield fpath
        for ext in os.environ.get("PATHEXT", "").split(os.pathsep):
            yield fpath + ext

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            for candidate in ext_candidates(exe_file):
                if is_exe(candidate):
                    return candidate

    return None


