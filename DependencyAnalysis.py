#!/usr/bin/env python
'''
analysis of task dependencies
'''
import ETA
import datetime
import treelib
import plotly.express as px
import pandas as pd
import numpy as np

OUT_HTML = './rhel62_08-05-2020_TaskWaitsByFinishTime.html'
IN_JSON = './rhel62_08-05-2020.json'
DISTROS = ['rhel62-large']

class DepTaskTimes(ETA.TaskTimes):
    '''
    DepTaskTimes extends ETA.TaskTimes. It adds distro-filtering functionality,
    along with dependency-aware wait time analysis that calculates new fields.
    '''

    def __init__(self, in_json, time_fields):
        '''
        DepTaskTimes extends ETA.TaskTimes. It adds distro-filtering functionality,
        along with advanced dependency-crawling functionality.
        '''
        # due to the added functionality, 
        # this class requires a lot of different time fields.
        required_time_fields = [ 'create_time',
                            'scheduled_time',
                            'start_time',
                            'finish_time',
                            ]
        required_fields_missing = []
        for field in required_time_fields:
            if field not in time_fields:
                required_fields_missing.append(field)
        if required_fields_missing:
            raise ValueError("required fields missing: {}".format(required_fields_missing))

        super().__init__(in_json,time_fields)

    ##
    # screen task data 

    def tasks_with_fields(self,fields):
        ''' generator that returns tasks containing field in fields'''
        for task_id in self.tasks:
            missing_field = False
            for field in fields:
                if field not in self.tasks[task_id]:
                     missing_field = True 
            if not missing_field:
                yield self.tasks[task_id]

    def screen_tasks_by_field(self, field, values):
        ''' only returns tasks that match allowed values of field'''
        tasks = {x:[] for x in values}
        for task in self.tasks_with_fields:
            if task[field] in values:
               tasks[task[field]].append(task)
        return tasks

     def screen_task_by_distros(self, distros):
        ''' screen tasks by distros, screen out tasks with broken/nonexistent dependency info
        returns {distro:[tasks] for distro in distros}.

        WILL SILENTLY return nothing if tasks have no distro field, 
        validation should be done beforehand.

        distros:
            d = ['rhel62-large']
            Used to filter out "protagonist" tasks from a larger dump of tasks from all distros.
            This is useful when you only care about wait times for a couple of distros, but they
            have dependencies from multiple distros.

        '''
        return self.screen_tasks_by_field('distro', distros)

    def screen_task_by_builds(self, builds)
        ''' return tasks that belong to specified builds, 
        returns a dict of lists of tasks by build, one per build in builds

        WILL SILENTLY return nothing if tasks have no build field, 
        validation should be done beforehand.
        '''
        return self.screen_tasks_by_field('build', builds)

    ##
    # calculate additional fields to add to tasks

    def calculate_perfect_world_latency(self, task):
        ''' takes in a task and recursively determines the time to finish this task
        assuming the world is perfect, i.e., that every dependency task runs immediately
        and with infinitely scalable concurrent operation. It assumes task runtime will 
        be the same, which may or may not be accurate.
        This has side effects on self.tasks, namely it will add 'perfect_world_latency' field to tasks.
        '''
        sentinel = datetime.timedelta(-1)
        if task == 'missingDep':
            return sentinel
        if 'perfect_world_latency' in task:
            return task['perfect_world_latency']
        else:
            #calculate it
            dependency_ids = [x['_id'] for x in task['depends_on']]
            dependency_times = [calculate_perfect_world_latency(self.tasks.get(tid,'missingDep')) for tid in dependency_ids]
            run_time = task['finish_time'] - task['start_time']
            if dependency_times:
                time_so_far = max(dependency_times)
                if time_so_far == sentinel :
                    #sentinel value, dep was missing
                    task['perfect_world_latency'] = sentinel
                    return sentinel
            else:
                time_so_far = datetime.timedelta(0)
            total_time = plus(time_so_far,run_time)
            task['perfect_world_latency'] = total_time
            return total_time

    def calculate_unblocked_time(self, task):
        ''' finds last dependency to finish, and adds this finish time to task
        as "unblocked_time". Returns true if this operation is completed.
        '''
        depends_on = task['depends_on']       
        # only add field if it is coherent to do so
        if depends_on:
            # we only care about finish times after this job has been scheduled
            latest_finish = task['scheduled_time']
            for dependency in depends_on:
                task_id = dependency['_id']
                finish_time = False
                if task_id in self.tasks:
                    finish_time = self.tasks[task_id]['finish_time']
                if finish_time and latest_finish < finish_time:
                    latest_finish = finish_time
            # only add field if it is coherent to do so
            if latest_finish != task['scheduled_time']:
                task['unblocked_time'] = latest_finish
                return True
        return False
                 
    @staticmethod 
    def calculate_latency_slowdown(task): 
        ''' adds 'latency_slowdown' field to task '''

        proportion_of_ideal = (task['finish_time'] - task['create_time']) / task['perfect_world_latency']
        if proportion_of_ideal > 0:
            task['latency_slowdown'] = proportion_of_ideal
        else:
            task['latency_slowdown'] = np.nan

    ##
    # display statistics

    def percent_tasks_with_deps(self):
        '''returns percent (out of 100) of tasks with nonempty dependency lists'''
        total_tasks = 0
        tasks_with_deps = 0
        for _id in self.tasks:
            task = self.tasks[_id]
            if task['depends_on']:
                tasks_with_deps += 1
            else:
                print(task)
            total_tasks +=1
        return tasks_with_deps / total_tasks 

     def wait_blocked_totals(self):
        total_wait_time = datetime.timedelta(0)
        total_time_blocked = datetime.timedelta(0)
        total_time_unblocked_waiting = datetime.timedelta(0)
        for task_id in self.tasks:
            task = self.tasks[task_id]
            if self.calculate_unblocked_time(task):
                total_wait_time += task['start_time'] - task['scheduled_time']
                total_time_blocked += task['unblocked_time'] - task['scheduled_time']
                total_time_unblocked_waiting += task['start_time'] - task['unblocked_time']
        print('{} total wait time'.format(total_wait_time))
        print('{} total time blocked'.format(total_time_blocked))
        print('{} total time unblocked_waiting'.format(total_time_unblocked_waiting))

    ##
    # figure generation 

    def generate_hist_wait_time(self):
        ''' returns histogram of wait times''' 
        return self.generate_hist('wait_time','scheduled_time','start_time')

    def generate_hist_turnaround_time(self):
        ''' returns histogram of turnaround times''' 
        return self.generate_hist('turnaround_time','scheduled_time','finish_time')

    def generate_hist_blocked_time(self):
        ''' returns histogram of blocked times''' 
        return self.generate_hist('blocked_time','scheduled_time','unblocked_time')

    def generate_hist(self, title, start_key, end_key):
        finish_times = []
        total = datetime.timedelta(0)
        total_hours = 0
        total_count = 0
        for task in self.tasks_with_fields([start_key,end_key]):
            time_delta = task[end_key] - task[start_key]
            seconds_in_minute = 60
            minutes_in_hour = 60
            time_delta_hour = (time_delta.seconds / seconds_in_minute) / minutes_in_hour
            finish_times.append({title:time_delta_hour})
            total_hours += time_delta_hour
            total += time_delta
            total_count += 1

        df = pd.DataFrame(finish_times)
        fig = px.histogram(df, x=title)
        print(total/total_count)
        print(total_hours/total_count)
        return fig

    def generate_gantt_from_task(task):

def chunked_mean_slowdown(time_chunked_tasks):
    ''' calculates average slowdown across each chunk given'''
    slowdowns = {}
    for chunk in time_chunked_tasks:
        tasks = time_chunked_tasks[chunk]
        latency_sum = datetime.timedelta(0)
        perfect_world_latency_sum = datetime.timedelta(0)
        for task in tasks:
            latency_sum += task['finish_time'] - task['create_time']
            perfect_world_latency_sum += task['perfect_world_latency'] 
        slowdowns[chunk] = latency_sum / perfect_world_latency_sum
    return slowdowns

class DepGraph:
    ''' contains data structures and methods for more directly manipulating DAG dependency graphs
    something like graph-tools would be useful for heavy-duty graph analysis, but here we want to use
    abstract indices for ease of lookup. Requires tasks dict with depends_on elements
    '''
    def __init__(self, tasks):
        size = len(tasks)
        self._depends_on_adjacency = np.zeros((size, size))
        self._task_ids = tasks.keys()
        # construct DAG adjacency matrix
        for _id in tasks:
            task = tasks[_id]
            depends_on = [x['_id'] for x in task['depends_on']]
            if depends_on:
                for key in depends_on:
                    i = self._task_ids.index(_id)
                    j = self._task_ids.index(key)
                    self._depends_on_adjacency[i][j] = 1

        # transpose to get the adjacency matrix for dependents
        # where all directed edges are reversed
        self._dependent_of_adjacency = self._depends_on_adjacency.transpose()


    def get_task_id_direct_depends_on(self, task_id):
        ''' this is more a sanity check than anything'''
        return self._get_task_id_adj(self._depends_on_adjacency, task_id)

    def get_task_id_direct_dependent_of(self, task_id):
        '''gets the reverse of depends_on'''
        return self._get_task_id_adj(self._dependent_of_adjacency, task_id)

    def _get_task_id_adj(self, adj, task_id):
        i = self._task_ids.index(task_id)
        direct_dependencies = []
        for j in adj[i]:
            if j == 1:
                direct_dependencies.append(self._task_ids[j])
        return direct_dependencies

    def get_depends_on_task_id_tree(self, task_id):
        ''' stub '''
        pass

    def get_dependent_of_task_id_tree(self, task_id):
        '''breadth first search of dependents of task specified by task_id'''

    def _bfs_task_id_adj(self, adj, task_id)

        tree = treelib.Tree()
        tree.create_node(task_id, task_id)
        current_level = {_id:[task_id] for _id in self._get_task_id_adj(adj, task_id)}
        while current_level:
            next_level = {}
            for child_id in current_level:
                parent_id = current_level[child_id]
                tree.create_node(child_id, child_id, parent=parent_id)
                grandchildren = {_id:child_id for _id in self._get_task_id_adj(adj, child_id)} 


            next_level = []
            _id = current_level.pop()
            parent = _id
            next_level = {}
            for item in next_leve
            current_level = {task_id:_id for _id in self._get_task_id_adj(adj, task_id)}

    def get_dependent_of_task_id_tree(self, task_id):
        '''breadth first search of dependents of task specified by task_id'''
        

def main():
    time_fields = [ 'create_time',
                    'scheduled_time',
                    'dispatch_time',
                    'start_time',
                    'finish_time',
                    ]

    task_data = DepTaskTimes(IN_JSON, time_fields)
    task_data.wait_blocked_totals()
    fig = task_data.generate_hist_wait_time()
    fig.show()

    fig = task_data.generate_hist_turnaround_time()
    fig.show()

    fig = task_data.generate_hist_blocked_time()
    fig.show()

if __name__ == '__main__':
    main()
