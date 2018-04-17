from multiprocessing import Process, Manager
from multiprocessing.managers import BaseManager
import time
import constants


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
        


class BackendServer(Process):
    def __init__(self, interval=15):
        super(BackendServer, self).__init__()
        self.interval = interval
        self.manager  = Manager()
        self.output_dict  = self.manager.dict()
        self.output_dict['nodes']        = []
        self.output_dict['nodes_header'] = {}
        self.output_dict['jobs']         = []
        self.output_dict['jobs_header']  = {}
        self.output_dict['tasks']        = []
        self.output_dict['tasks_header'] = {}
        self.output_dict['running_tasks']        = []
        self.output_dict['running_tasks_header'] = {}
        self.commander = Slurm()

    def get_key(self, key):
        if key in self.output_dict:
            return self.output_dict[key]
        return {}

    def update(self, nodes=True, running=True, jobs=True, tasks=True):
        from sys import exit
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
        except:
            print "Exiting backend server bye, bye..."
            exit()
        
    def run(self):
        while(True):
            self.update()
            time.sleep(self.interval)