import os

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


def clamp(value, _min, _max):
    if value > _max: return _max
    if value < _min: return _min
    return value
        
        
def fit(x, a, b, c, d):
    return c+((x-a)/(b-a))*(d-c)


def string_to_elapsed_time(value):
    '''Returns time difference provided SGE specific string time.'''
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
    from os import getuid
    from  pwd import getpwuid
    return getpwuid(getuid())[0]
