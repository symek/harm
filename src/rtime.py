#!/usr/bin/python

#Imports:
import os, sys
from optparse import OptionParser

# I'm so lazy:
#http://stackoverflow.com/questions/775049/python-time-seconds-to-hms
def getInHMS(seconds):
   '''Converts seconds to a time string HH:MM:SS'''
    hours = seconds // 3600.0
    seconds -= 3600.0*hours
    minutes = seconds // 60.0
    seconds -= 60.0*minutes
    return "%02d:%02d:%02d" % (hours, minutes, seconds)


def parseOptions():
   """Parse command line options"""
    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage)
    #Options:
    parser.add_option("-s", "--stat", dest="stat",  action="store_true",  help="Print general statistics (not implemented).")
    parser.add_option("-u", "--user", dest="user",  action="store",  help="Overwrites user.")
    parser.add_option("-j", "--jobid", dest="jobid",  action="store",  help="Specifiy job id.")
    parser.add_option("-d", "--days", dest="days",  action="store",  default = 1, help="Displays job history with specified peried (1=today, 2=from yestarday, etc.")
    (opts, args) = parser.parse_args(sys.argv[1:])
    return opts, args, parser


def job_details(job_id):
    """Prints per frame statistics."""
    pass



def job_statistics(job_id, days):
    """Prints details from the SGE 'qacct' utility, which reads the history file of task."""
    data = os.popen("qacct -d %s -j %s" % (days, job_id)).readlines()
    if not data: return

    # Our data center ;)
    details = {}
    details['cpu'] = []
    details['mem'] = []
    details['frames'] = 0
    details['current_render'] = []
    details['jobname'] = ''
    details['job_array'] = '0-0:1'

    # Get jobname:
    for line in data:
        line = line.strip()
        if line.startswith("jobname"):
            details['jobname'] = line[7:].strip()
            break

    # Get job details:
    job_details = os.popen("qstat -j %s" % job_id).readlines()
    for line in job_details:
        if line.startswith("job-array"):
            details['job_array'] = line[16:].strip()
        if line.startswith("owner"):
            details['owner'] = line[6:].strip()
        if line.startswith("usage"):
            details['current_render'] += [line.split(":")[0][5:].strip()]
            

    # Get details of usage:
    for line in data:
        line = line.strip()
        if line.startswith("cpu"):
            details['cpu'] += [float(line[3:])]
        if line.startswith("mem"):
            details['mem'] += [float(line[3:].strip())]
            details['frames'] += 1

    # Compute some more details:
    details['avarage_cpu'] = sum(details['cpu']) / len(details['cpu'])
    details['avarage_mem'] = sum(details['mem']) / len(details['mem'])
    details['eta']         = (int(details['job_array'].split(":")[0].split("-")[1]) - int(details['frames'])) * details['avarage_cpu']
    #print details['job_array']

    print
    print "Jobid: %s" % job_id
    print "Job  : %s" % details['jobname']
    print "Owner: %s " % details['owner']
    print "                 MIN            MAX            AVG    " 
    print "=========================================================="
    print " CPU:        %s         %s        %s         " % (str(getInHMS(min(details['cpu'])/10.0)), 
                                                        str(getInHMS(max(details['cpu'])/10.0)),
                                                        str(getInHMS(details['avarage_cpu']/10.0)))

    print " MEM:        %s        %s      %s         " % (str(min(details['mem'])/10)[:6] + " MB", 
                                                                          str(max(details['mem'])/10)[:6] + ' MB',
                                                                          str(details['avarage_mem']/10)[:6] + ' MB')
    print 
    print "Frames complated: %s" % details['frames']
    print "Frames pending  : %s"  % str(int(details['job_array'].split(":")[0].split("-")[1]) - int(details['frames']))
    print "Currently render: %s, (%s active)" % (", ".join(details['current_render']), len(details['current_render']))
    print "Estimated finish: %s" % str(getInHMS(details['eta'] / 10.0 / len(details['current_render'] ))) + " (avarage_time * pending_frames / active_machines )"
     
     


def get_user_jobs(user):
    """This returns a jobids for currently running jobs."""
    data = os.popen('qstat -u "%s"' % user).readlines()
    data = [line.split() for line in data]
    data = [line for line in data if 'r' in line]
    job_ids = [line[0].strip() for line in data if line[0].isdigit()]
    return list(set(job_ids))
    
    


def main():
    '''Print statistics of SGE jobs'''

    # Parse settings:
    opts, args, parser = parseOptions()

    # Me if not specified:
    if not opts.user:
        opts.user = os.getenv("USER", "*")

    # Job id wa specified:
    if opts.jobid:
        job_statistics(opts.jobid, opts.days)

    # Or we want all jobs of an user:
    else:
        job_ids = get_user_jobs(opts.user)
        for id in job_ids:
            job_statistics(id, opts.days)
        
  
if __name__ == "__main__": main()




