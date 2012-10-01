from xml.etree.ElementTree import ElementTree, tostring
import structured as stc

def getValue(value):
    if value.isdigit(): 
        value = int(value)
    try: 
        value = float(value)
    except: 
        pass
    return value


def parse_text(text, tasks=False):
    f = text.split(62*"=")
    out = {}
    et = ElementTree()
    for job in f:
        j = {}
        job = job.split("\n")
        for tag in job:
            tag = tag.strip().split()
            if len(tag) > 1:
                j[tag[0]] = getValue(" ".join(tag[1:]))
        if j.keys():
            if not tasks:
                out[str(j['jobnumber'])] = j
            else:
                out[".".join([str(j['jobnumber']), str(j['taskid'])])] = j
    return out
