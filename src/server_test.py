#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
import os
import xmltodict
from couchdb import Server
from constants import *
from xml.etree.ElementTree import ElementTree
from collections import defaultdict


server = Server(os.getenv("CDB_SERVER"))
print server

db  = 'sge_db'

if db in server:
    db = server[db]
else:
    db = server.create(db)

print db

xml = os.popen(SGE_JOBS_LIST).read()
xml2= os.popen(SGE_CLUSTER_LIST).read()
#etree  = ElementTree()
#etree.parse(xml)
jobs = xmltodict.parse(xml)['job_info']
hist = xmltodict.parse(xml2)
#print jobs

sig = 'sge_jobs_list'
if not sig in db:
    db[sig] = jobs
    jobs = db[sig]   
else:
    doc = db[sig]
    for key in jobs:
        doc[key] = jobs[key]
    db[sig] = doc



sig = 'sge_cluster_list'
if not sig in db:
    db[sig] = hist
    doc = db[sig]   
else:
    doc = db[sig]
    for key in hist:
        doc[key] = hist[key]
    db[sig] = doc


print doc

