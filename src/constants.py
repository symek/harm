
# Constants:
SGE_JOB_DETAILS         = 'qstat -ext -f -xml -j %s'
SGE_JOBS_LIST_GROUPED   = 'qstat -xml -u "*"'
SGE_JOBS_LIST           = 'qstat -xml -g d -u "*"'
SGE_CLUSTER_LIST        = 'qhost -xml -j'
SGE_HISTORY_LIST        = 'qacct -d 3 -j "*"'
SGE_HISTORY_JOB         = 'qacct -d 3 -j %s'
SGE_HISTORY_JOB_LAST    = 'qacct -d 1'

EMPTY_SGE_JOB_DETAILS   = 'cat empty_job_details.xml'

# Work in idle (no SGE around)
#SGE_JOB_DETAILS         = 'cat jobDetails.xml'
#SGE_JOBS_LIST_GROUPED   = 'cat jobsListGrouped.xml'
#SGE_JOBS_LIST           = 'cat jobsListed.xml '
#SGE_CLUSTER_LIST        = 'cat clusterList.xml'


SGE_HOST_RAM_WARNING   = .95 # Percent of RAM beyond which host is marked in red.
SGE_HOST_SWAP_WARNING  = .05 # Amout of SWAP usage beyond which host is marked in red.
