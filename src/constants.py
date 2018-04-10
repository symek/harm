
# SGE commands:
SGE_JOB_DETAILS         = 'qstat -ext -g d -t -f -pri -xml -j %s'
SGE_JOBS_LIST_GROUPED   = 'qstat -xml -u "*"'
SGE_JOBS_LIST           = 'qstat -xml -g d -u "*"'
SGE_CLUSTER_LIST        = 'qhost -xml -j'
SGE_HISTORY_LIST        = 'qacct -d 3 -j "*"'
SGE_HISTORY_JOB         = 'qacct -d 3 -j %s'
SGE_HISTORY_JOB_LAST    = 'qacct -d 1'

#SGE_COMMANDS:
SLURM_JOBS_LIST_GROUPED  = 'squeue -t PD -o "%F %P %u %T %j %V %e %M %K %A"'
SLURM_JOBS_LIST          = 'squeue -j <JOBID/> -t PD,R,C,PR -r -o "%K %P %u %T %r %S %e %M %B %A"'
SLURM_TASK_DETAILS        = 'scontrol show job <JOBID/>_<TASKID/>'
SLURM_JOB_DETAILS        = 'scontrol show job <JOBID/>'
SLURM_CLUSTER_LIST       = 'scontrol show nodes -o'
SLURM_RUNNING_JOBS_LIST  = 'squeue -t R -r -o "%A %K %P %B %u %T %j %V %M %w %W %X %z %o"'
 
EMPTY_SGE_JOB_DETAILS   = 'cat empty_job_details.xml'

# Work in idle (no SGE around)
#SGE_JOB_DETAILS         = 'cat jobDetails.xml'
#SGE_JOBS_LIST_GROUPED   = 'cat jobsListGrouped.xml'
#SGE_JOBS_LIST           = 'cat jobsListed.xml '
#SGE_CLUSTER_LIST        = 'cat clusterList.xml'

# Color settings for delegates:
SGE_HOST_RAM_WARNING   = .95 # Percent of RAM beyond which host is marked in red.
SGE_HOST_SWAP_WARNING  = .05 # Amout of SWAP usage beyond which host is marked in red.


# Nuke ReadNode string:
NUKE_READ_NODE_STRING = '''Read {
        				inputs 0
        				file %s
        				format "1280 720 0 0 1280 720 1 "
        				first %s
        				last  %s
        				origset true
        				name Read1
        				selected true
        				xpos -221
        				ypos -160 }'''

# Debug or nor to debug?
import os
DEBUG = os.getenv("DEBUG", False)



# Design documents.
# TODO: Perhaps it would be better it keep them as *.json 
# files and feed/update database with curl/wget calls?
# Even of not, they should belong to some sort of Datase module...

harm_views = dict()
harm_views['get_jobs_db'] = '''function(doc) {
                    var js  = doc.JB_ja_structure.task_id_range;
                    var jss = "".concat(js.RN_min, "-", js.RN_max, ":", js.RN_step);
                    var que = doc.JB_hard_queue_list.destin_ident_list.QR_name;
                    emit(doc._id, [doc.JB_owner, "cdb", jss, doc.JB_priority, doc.JB_job_name, 
                             "1", que, doc.JB_job_number, doc.JB_submission_time]);}'''

harm_views['get_tasks_db'] = '''function(doc) 
{
  if (doc.JB_ja_tasks.ulong_sublist)
  {
        var tasks    = new Array();
        var sublist  = doc.JB_ja_tasks.ulong_sublist;
        for(var task = 0; task < sublist.length; task++)
        {
                var scaled = sublist[task].JAT_scaled_usage_list.scaled;
                var names  = new Array();
                var values = new Array();
                for (var item = 0; item < scaled.length; item++)
                {
                        names[item]  = scaled[item].UA_name; 
                        values[item] = scaled[item].UA_value;
                }
                tasks[task] = (names, values);
        }
        emit(doc._id, tasks);     
  }

}'''
        
