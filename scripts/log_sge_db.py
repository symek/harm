#!/usr/bin/python
from couchdb import Server
import sys, os
sys.path.append("/STUDIO/scripts/harm-sge-db/src")
from models import JobDetailModel, XmlDictConfig
from constants import *
import utilities
from xml.etree import ElementTree

class Model:
	pass

db    = 'sge_db'
jobid = sys.argv[1]

server = Server(os.getenv("CDB_SERVER"))


if db in server:
    db = server[db]
else:
    db = server.create(db)


#model = JobDetailModel()
#model.update(SGE_JOB_DETAILS % jobid, 'djob_info')
#print dict(model._dict)
tree = ElementTree.parse(os.popen(SGE_JOB_DETAILS % jobid))
_dict  = XmlDictConfig(tree.getroot())#['djob_info']['element']
#model = utilities.formatXML(os.popen(SGE_JOB_DETAILS % jobid))
model = Model()
model._dict = _dict

#'''

for key in model._dict:
	if key.startswith("__"):
		nkey  = key[2:]
	elif key.startswith("_"):
		nkey = key[1:]
	else:
		continue
	value = model._dict.pop(key)
	model._dict[nkey] = value


if not jobid in db:
	db[jobid] = dict(model._dict)
	job       = db[jobid]
else:
	job       = db[jobid]
	for key in model._dict:
		job[key] = model._dict[key]
	db[jobid] = job


