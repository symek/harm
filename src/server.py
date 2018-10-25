from multiprocessing import Process, Manager
from multiprocessing.managers import BaseManager
import time
import constants
import logging

class BackendCommander(object):
    pass

class Slurm(BackendCommander):
    RUNNING_JOBS_LIST  = 'squeue -t R -r -o "%A %K %P %B %u %T %j %V %M %w %W %X %z %o"'
    def get_nodes_info(self, node=None, reverse_order=False):
        import slurm
        return slurm.get_nodes_info()

    def get_current_jobs(self, length, reverse_order=True):
        import slurm
        return slurm.get_current_jobs(length, reverse_order)

    def get_running_tasks_info(self):
        def parse_slurm_output(output):
            lines = output.split("\n")
            if len(lines) == 1: lines  += [""]
            head, lines = lines[0], lines[1:]
            head = [word.strip() for word in head.split()]
            lines = [line.split() for line in lines if line]
            return lines, head

        import subprocess
        err = None
        data = []
        head = {}

        out, err =subprocess.Popen(self.RUNNING_JOBS_LIST, shell=True, \
        stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
        if out:
            data, header = parse_slurm_output(out)
            for item in header:
                head[header.index(item)] = item

        return data, head

    def get_job_tasks(self, jobid):
        import slurm
        return slurm.get_job_tasks(jobid)
        


class BackendServer(Process):
    def __init__(self, interval=15):
        super(BackendServer, self).__init__()
        logging.basicConfig(format='%(asctime)s, %(name)s - %(levelname)s: %(message)s',  
            datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)

        self.interval  = interval
        self.manager   = Manager()
        self.output_dict  = self.manager.dict()
        self.output_dict['nodes']        = []
        self.output_dict['nodes_header'] = {}
        self.output_dict['jobs']         = []
        self.output_dict['jobs_header']  = {}
        self.output_dict['tasks']        = {}
        self.output_dict['tasks_header'] = {}
        self.output_dict['running_tasks']        = []
        self.output_dict['running_tasks_header'] = {}
        self.output_dict['timestamp'] = 0.0

        self.commander = Slurm()

    def get_by_key(self, key, jobid=None):
        """ Amortized getter. Simple approach (no decorators etc.)
            Single timestamp for now. WIP.
        """
        # For tasks:
        if key == 'tasks' and jobid:
            if not jobid in self.output_dict['tasks'].keys():
                self.logger.debug("Fresh tasks query")
                self._update_job_tasks(jobid)
            elif time.time() - self.output_dict['timestamp']  > self.interval:
                self.logger.debug("Tasks outdated, refresing it...")
                self._update_job_tasks(jobid)

            assert(jobid in self.output_dict['tasks'])
            return self.output_dict['tasks'][jobid]

        # Anything else:
        if key in self.output_dict:
            return self.output_dict[key]
        return {}

    def _update_job_tasks(self, jobid):
        """
        """
        self.logger.debug("Updating tasks...")
        _data, _header = self.commander.get_job_tasks(jobid)

        if None in (_data, _header):
            self.logger.error("Can't import tasks info for job: %s" % str(jobid))
            return False

        self.logger.debug("Updating tasks done for job: %s" % str(jobid))
        _tmp = dict(self.output_dict['tasks'])
        _tmp[jobid] = _data
        self.output_dict['tasks'] = dict(_tmp)

        # Don't do it twise:
        if not self.output_dict['tasks_header']:
            self.logger.debug("Creating tasks header.")
            self.output_dict['tasks_header'] = _header
        return True

    def update(self, nodes=True, running=True, jobs=True, tasks=True):
        from sys import exit
        self.logger.debug("Updating data...")
        if jobs:
            pending, pending_header = self.commander.get_current_jobs(1500, True)
        if nodes:
            _nodes, nodes_header = self.commander.get_nodes_info()
        if running:
            tasks, tasks_header = self.commander.get_running_tasks_info()
        try:
            self.output_dict['jobs']= pending
            self.output_dict['jobs_header'] = dict(pending_header)
            self.output_dict['nodes']= _nodes
            self.output_dict['nodes_header'] = dict(nodes_header)
            self.output_dict['running_tasks']        = tasks
            self.output_dict['running_tasks_header'] = dict(tasks_header)
            self.output_dict['timestamp'] = time.time()
            self.logger.debug("Updating data ended.")
        except:
            self.logger.error("Can't update data...")
            print "Exiting backend server bye, bye..."
            exit()

    def terminate(self):
        self.logger.info("Exiting backend server bye, bye...")
        self.process.terminate()
        
    def run(self):
        self.logger.debug("Going into while(True) loop")
        while(True):
            self.update()
            time.sleep(self.interval)