#!/usr/bin/env python
'''
analysis of task dependencies
'''
import datetime
import ETA
import igraph
import logging
import multiprocessing
import plotly.express as px
import pandas as pd
import numpy as np

OUT_HTML = './WT_gantt.html'
#IN_JSON = './wiredtiger_ubuntu1804_89a2e7e23a18fa5889e38a82d1fc7514ae8b7b93_20_05_06_04_57_20-tasks.json'
IN_JSON = './sept21rhel62small.json'

class DepWaitTaskTimes(ETA.TaskTimes):
    '''
    DepWaitTaskTimes extends ETA.TaskTimes. It adds dependency-aware wait time analysis that calculates new fields.
    '''

    def __init__(self, in_json, time_fields):
        '''
        DepWaitTaskTimes extends ETA.TaskTimes. It adds distro-filtering functionality,
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
    # calculate additional fields to add to tasks

    def calculate_task_perfect_world_latency(self, task):
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
            dependency_times = [calculate_task_perfect_world_latency(self.tasks.get(tid,'missingDep')) for tid in dependency_ids]
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

    def calculate_task_unblocked_time(self, task):
        ''' finds last dependency to finish, and adds this finish time to task
        as "unblocked_time". Returns true if this operation is completed.
        Also generates 'begin_wait' time, which is either unblocked time or scheduled time,
        as appropriate.
        '''
        depends_on = task['depends_on']       
        # only add field if it is coherent to do so
        if task['start_time'] < task['scheduled_time'] :
            logging.debug('bad time for {}'.format(task))
            return False
        if depends_on:
            # we only care about finish times after this job has been scheduled
            latest_finish = task['scheduled_time']
            for dependency in depends_on:
                task_id = dependency['_id']
                finish_time = False
                if task_id in self.tasks:
                    finish_time = self.tasks[task_id]['finish_time']
                else:
                    # incomplete information
                    logging.debug('incomplete info')
                    return False
                if finish_time and latest_finish < finish_time and finish_time < task['start_time']:
                    latest_finish = finish_time
            # only add field if it is coherent to do so
            if latest_finish != task['scheduled_time'] :
                task['unblocked_time'] = latest_finish
                task['begin_wait'] = latest_finish
                return True
        #if we're here, didn't set 'unblocked_time'
        task['begin_wait'] = task['scheduled_time']
        return False

    @staticmethod 
    def calculate_task_latency_slowdown(task): 
        ''' adds 'latency_slowdown' field to task '''

        proportion_of_ideal = (task['finish_time'] - task['create_time']) / task['perfect_world_latency']
        if proportion_of_ideal > 0:
            task['latency_slowdown'] = proportion_of_ideal
        else:
            task['latency_slowdown'] = np.nan

    ##
    # display statistics

    def display_percent_tasks_with_deps(self):
        '''returns percent (out of 100) of tasks with nonempty dependency lists'''
        total_tasks = 0
        tasks_with_deps = 0
        for task in self.get_tasks():
            if task['depends_on']:
                tasks_with_deps += 1
            else:
                print(task)
            total_tasks +=1
        return tasks_with_deps / total_tasks 

    def display_wait_blocked_totals(self):
        ''' display total time waiting, blocked, and unblocked waiting 
        for the entire data set.
        Has the side effect of calculating unblocked time, 
        which creates 'begin_wait' and 'unblocked_time' fields'''
        total_wait_time = datetime.timedelta(0)
        total_time_blocked = datetime.timedelta(0)
        total_time_unblocked_waiting = datetime.timedelta(0)
        for task in self.get_tasks():
            if self.calculate_task_unblocked_time(task):
                total_wait_time += task['start_time'] - task['scheduled_time']
                total_time_blocked += task['unblocked_time'] - task['scheduled_time']
                total_time_unblocked_waiting += task['start_time'] - task['unblocked_time']
        print('{} total wait time'.format(total_wait_time))
        print('{} total time blocked'.format(total_time_blocked))
        print('{} total time unblocked_waiting'.format(total_time_unblocked_waiting))

    def display_worst_unblocked_wait_per_field(self, field):
        ''' at present this only looks at unblocked wait time for tasks which have dependencies.
        This is inaccurate, as all tasks without dependencies are unblocked when they are scheduled.
        '''
        generator = self.get_tasks({'start_time':[],'begin_wait':[]})
        tasks_by_field = self.bin_tasks_by_field(field, task_generator=generator)
        worst_waits = {}
        worst_wait_ids = {}
        for field_key in tasks_by_field:
            worst_wait = datetime.timedelta(0)
            worst_task_id = None
            for task in tasks_by_field[field_key]:
                value = task['start_time'] - task['begin_wait']
                if value > worst_wait:
                    worst_wait = value
                    worst_task_id = task['_id']
            if worst_task_id:
                worst_waits[field_key] = worst_wait
                worst_wait_ids[field_key] = worst_task_id 

        longest_waits_first = dict(sorted(worst_waits.items(), key=lambda item: item[1],reverse=True))
        for field in longest_waits_first:
            if field in worst_wait_ids:
                print('{} {} {}'.format(worst_waits[field],field, worst_wait_ids[field]))
    ##
    # figure generation 

    def generate_hist_raw_wait_time(self):
        ''' returns histogram of wait times''' 
        return self.generate_hist('raw_wait_time','scheduled_time','start_time')
    
    def generate_hist_corrected_wait_time(self):
        ''' returns histogram of wait times, corrected for dependencies''' 
        return self.generate_hist('corrected_wait_time','begin_wait','start_time')

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
        first_time = True 
        title = title + '(hours)'
        for task in self.get_tasks({start_key:[],end_key:[]}):
            time_delta = task[end_key] - task[start_key]
            seconds_in_minute = 60
            minutes_in_hour = 60
            time_delta_hour = (time_delta.seconds / seconds_in_minute) / minutes_in_hour
            finish_times.append({title:time_delta_hour})
            total_hours += time_delta_hour
            total += time_delta
            total_count += 1
            if first_time:
                worst = {time_delta_hour:task}
                first_time = False
            if time_delta_hour > next(iter(worst)):
                worst = {time_delta_hour:task}
        df = pd.DataFrame(finish_times)
        fig = px.histogram(df, x=title)
        return fig

def generate_task_depends_on_gantt():

    pass

def generate_task_dependent_of_gantt():

    pass

class DepGraph:
    ''' contains data structures and methods for more directly manipulating DAG dependency graphs
    something like graph-tools would be useful for heavy-duty graph analysis, but here we want to use
    abstract indices for ease of lookup. Requires tasks dict with depends_on elements.
    Main benefit is neighborhood analysis and more advanced graph algorithms and functionality.
    '''
    def __init__(self, tasks):
        size = len(tasks)
        self._depends_on_adjacency = np.zeros((size, size))
        self._task_ids = list(tasks.keys())
        task_list = list(tasks.values())

        # construct DAG adjacency matrix
        for task in task_list:
            self._update_adjacent_vertices(task)

        # convert to igraph for advanced graph algos and visualization
        self._depends_on_graph = igraph.Graph.Adjacency(self._depends_on_adjacency.tolist())
        self._depends_on_graph.vs['label'] = [x for x in range(size)]
        for i,x in enumerate(self._task_ids):
            print('{} {}'.format(i,x))

    def _update_adjacent_vertices(self, task):
            
        _id = task['_id']
        depends_on = [x['_id'] for x in task['depends_on']]
        if depends_on:
            for key in depends_on:
                if key in self._task_ids:
                    i = self._task_ids.index(_id)
                    j = self._task_ids.index(key)
                    print('{} depends on {}'.format(_id,key))
                    self._depends_on_adjacency[i][j] = 1

    def get_task_id_direct_depends_on(self, task_id):
        ''' this is more a sanity check than anything'''
        return _neighborhood("out", 1, task_id) 

    def get_task_id_direct_dependent_of(self, task_id):
        '''gets the reverse of depends_on'''
        return _neighborhood("in", 1, task_id) 

    def _reachable(self, direction, task_id):
        # note: the longest path to any vertex goes through every vertex in the graph,
        # hence order=len(self._task_ids)
        return _neighborhood(direction, len(self._task_ids), task_id)

    def _neighborhood(self, direction, order, task_id):
        vertex_id = self._task_ids.index(task_id)
        vertex_list = self._depends_on_graph.neighborhood(vertex_id,order,direction)
        task_id_list = [self._task_ids[i] for i in vertex_list]
        return task_id_list

    def get_depends_on_task_id(self, task_id):
        '''returns all tasks that the specified task depends on. 
        In other words, returns all verticies of the depends_on graph reachable from
        the vertex identified by task_id.'''
        return self._reachable("out",task_id)

    def get_dependent_of_task_id_dag(self, task_id):
        '''returns all tasks that is a dependent of the specified task. 
        In other words, returns all verticies of the depends_on graph reachable from
        the vertex identified by task_id.'''
        return self._reachable("in",task_id)

    def generate_depends_on_graph_diagram(self, task_ids=None):
        '''returns an igraph plot of the depends_on subgraph formed by the vertices in task_ids,
        or if task_ids is None(default), displays the entire graph. 
        plot can be visualized with p.show()'''

        if task_ids:
            if isinstance(task_ids,str):
                task_ids = [task_ids]
            vertex_ids = [self._task_ids.index(task_id) for task_id in task_ids]
            subgraph = self._depends_on_graph.induced_subgraph(vertex_ids)
        else:
            subgraph = self._depends_on_graph

        p = igraph.plot(subgraph)
        
        return p

def main():
    time_fields = [ 'create_time',
                    'scheduled_time',
                    'dispatch_time',
                    'start_time',
                    'finish_time',
                    ]

    task_data = DepWaitTaskTimes(IN_JSON, time_fields)
    task_data.display_wait_blocked_totals()
    task_data.screen_by = {'build_id': ['mongodb_mongo_v4.2_enterprise_suse12_64_220d72da13180652f4986bc65a0dd95966973dd0_20_09_14_17_52_50']}

    fig = task_data.generate_hist_corrected_wait_time()
    fig.show()

    graph = DepGraph({x["_id"]:x for x in task_data.get_tasks()})
    g = graph.generate_depends_on_graph_diagram()


if __name__ == '__main__':
    main()
