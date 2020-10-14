#!/usr/bin/env python3
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

logging.basicConfig(level=logging.INFO)
IN_JSON = './foobar.json'

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
        required_time_fields = [ 
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
    # calculate additional fields and return value

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

    ##
    # calculate additional fields to add to tasks and update value in task

    def update_task_unblocked_time(self, task):
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
    def update_task_latency_slowdown(task): 
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
            if self.update_task_unblocked_time(task):
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
            for task in tasks_by_field[field_key].values():
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

    def display_version_slowdown(self, versions=None):

        allowed_distros = []
        for distro in self.bin_tasks_by_field('distro'):
            if 'power8' not in distro and 'zseries' not in distro:
                if distro not in allowed_distros:
                    allowed_distros.append(distro)

        generator = self.get_tasks({'scheduled_time':[],'start_time':[],'finish_time':[], 'distro':allowed_distros})

        tasks_by_version = self.bin_tasks_by_field('version', values=versions, task_generator=generator)
        slowdowns_by_version = {}
        for version in tasks_by_version:
            version_tasks = tasks_by_version[version]

            # set according to particular question you want to answer
            if len(version_tasks) < 1:
                continue
            try:
                slowdown = DepGraph.display_version_slowdown(version_tasks)
                slowdowns_by_version[version] = slowdown
            except ValueError:
                continue
        sorted_slowdowns_by_version  = {k: v for k, v in sorted(slowdowns_by_version.items(), key=lambda item: item[1])}
        for version in sorted_slowdowns_by_version:
            print('{}: {}'.format(sorted_slowdowns_by_version[version],version))

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
    def __init__(self, tasks, edge_weight_rule=None, verbose=None):

        self.verbose = verbose
        size = len(tasks)
        self._depends_on_adjacency = np.zeros((size, size))
        self._task_ids = list(tasks.keys())
        task_list = list(tasks.values())
        
        self.edge_weight_rule = edge_weight_rule

        # construct DAG adjacency matrix
        for task in task_list:
            self._update_adjacent_vertices(task)

        # convert to igraph for advanced graph algos and visualization
        self.depends_on_graph = igraph.Graph.Weighted_Adjacency(self._depends_on_adjacency.tolist())
        self.depends_on_graph.vs['label'] = [x for x in range(size)]
        if self.verbose:
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
                    if self.verbose:
                        print('{} depends on {}'.format(_id,key))
                    if self.edge_weight_rule:
                        weight = self.edge_weight_rule(task)
                    else:
                        weight = 1
                    self._depends_on_adjacency[i][j] = weight

    def get_task_id_direct_depends_on(self, task_id):
        ''' this is more a sanity check than anything'''
        return _neighborhood("out", 1, task_id) 

    def vertex_to_task_id(self, vertex_id):
        return self._task_ids[vertex_id]

    def get_task_id_direct_dependent_of(self, task_id):
        '''gets the reverse of depends_on'''
        return _neighborhood("in", 1, task_id) 

    def _reachable(self, direction, task_id):
        # note: the longest path to any vertex goes through every vertex in the graph,
        # hence order=len(self._task_ids)
        return _neighborhood(direction, len(self._task_ids), task_id)

    def _neighborhood(self, direction, order, task_id):
        vertex_id = self._task_ids.index(task_id)
        vertex_list = self.depends_on_graph.neighborhood(vertex_id,order,direction)
        task_id_list = [self._task_ids[i] for i in vertex_list]
        return task_id_list

    def get_depends_on_task_id(self, task_id):
        '''returns all tasks that the specified task depends on. 
        In other words, returns all verticies of the depends_on graph reachable from
        the vertex identified by task_id.'''
        return self._reachable("out",task_id)

    def get_dependent_of_task_id(self, task_id):
        '''returns every task that is a dependent of the specified task. 
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
            subgraph = self.depends_on_graph.induced_subgraph(vertex_ids)
        else:
            subgraph = self.depends_on_graph

        p = igraph.plot(subgraph)
        
        return p

    @classmethod
    def display_version_slowdown(cls, tasks):
        ''' calculates slowdown across version by finding the time a version would have taken to run if every task started
        as soon as its dependencies were met or as soon as it was scheduled, if no dependencies exist. It assumes task runtime would
        be the same.
        '''
        # make implicit dependency of generated on generator explicit
        generator_tasks = {}
        for task_id in tasks:
            if 'generated_by' in tasks[task_id]:
                generated_by = tasks[task_id]['generated_by']
                if generated_by in generator_tasks:
                    generator_tasks[generated_by].append(task_id)
                else:
                    generator_tasks[generated_by] = [task_id]

        for task_id in generator_tasks:
            dummy_id = task_id + '_dummygen'
            dummy_task = generator_tasks[task].copy()
            dummy_task['finish_time'] = dummy_task['start_time']
            dummy_task['_id'] = dummy_id
            tasks[dummy_id] = dummy_task

            dummy_dependency = {'_id':dummy_id}
            for dependent_id in generator_tasks[task_id]:
                if tasks[dependent_id]['depends_on']:
                    tasks[dependent_id]['depends_on'].append(dummy_dependency)

        # determine all vertices with outdegree 0 and indegree 0 
        task_ids_with_incoming_edges = set()
        task_ids_with_outgoing_edges = set()
        all_task_ids = set(tasks.keys())
        # also determine the earliest scheduled_time and latest finish_time
        earliest_scheduled = datetime.datetime.max
        latest_finish = datetime.datetime.min
        for task_id in tasks:
            scheduled = tasks[task_id]['scheduled_time']
            finish = tasks[task_id]['finish_time']
            if latest_finish < finish : 
                latest_finish = finish
            if scheduled < earliest_scheduled:
                earliest_scheduled = scheduled
            if tasks[task_id]['depends_on']:
                task_ids_with_outgoing_edges.add(task_id)
                for dep_task_item in tasks[task_id]['depends_on']:
                    dep_key = dep_task_item['_id']
                    if dep_key not in all_task_ids:
                        raise ValueError('incomplete task list. Dependency does not appear in task list: {}'.format(dep_key))
                    task_ids_with_incoming_edges.add(dep_key)

        real_version_latency_dt = latest_finish - earliest_scheduled
        print('{} is latest finish'.format(latest_finish))
        print('{} is earliest scheduled '.format(earliest_scheduled))
        real_version_latency_seconds = real_version_latency_dt.total_seconds()

        task_ids_with_zero_indegree = all_task_ids - task_ids_with_incoming_edges
        task_ids_with_zero_outdegree = all_task_ids - task_ids_with_outgoing_edges

        # add dummy tasks as entry points for mincost algorithm
        source_id = 'dummy_source'
        source_vertex = {'_id': source_id, 'depends_on':[{'_id':x} for x in task_ids_with_zero_indegree]}
        source_vertex['start_time'] = earliest_scheduled
        source_vertex['finish_time'] = earliest_scheduled + datetime.timedelta(seconds=1)
        source_vertex_id = len(tasks)
        tasks[source_id] = source_vertex

        target_id = 'dummy_target'
        target_vertex = {'_id': target_id, 'depends_on':[]}
        target_vertex['start_time'] = latest_finish 
        target_vertex['finish_time'] = latest_finish + datetime.timedelta(seconds=1)
        target_vertex_id = len(tasks)
        tasks[target_id] = target_vertex 
        for task_id in task_ids_with_zero_outdegree:
            try:
                tasks[task_id]['depends_on'].append({'_id': target_id})
            except KeyError:
                print(task_id)
                print(tasks[task_id])
                raise

        # call mincost_path

        def calculate_maxcost_path_weight(some_task):
            timedelta_weight = some_task['finish_time'] - some_task['start_time']
            seconds =  timedelta_weight.total_seconds()
            # invert to allow calculation of maxcost path by mincost-path algo
            return -1 * seconds

        depgraph = cls(tasks, calculate_maxcost_path_weight)
        idealized_latency = depgraph.depends_on_graph.shortest_paths_dijkstra(source=source_vertex_id, target=target_vertex_id, weights='weight')
        # have to multiply by -1 again to make the mincost path positive.
        idealized_latency_seconds = idealized_latency[0][0] * -1

        slowdown = real_version_latency_seconds/idealized_latency_seconds
        print('{} seconds or {} hours (actual)'.format(real_version_latency_seconds, real_version_latency_seconds/60**2))
        print('{} seconds or {} hours (idealized)'.format(idealized_latency_seconds, idealized_latency_seconds/60**2))
        print('{} is slowdown'.format(real_version_latency_seconds/idealized_latency_seconds))

        return slowdown

def main():
    time_fields = [ 
                    'scheduled_time',
                    'start_time',
                    'finish_time',
                    ]

    task_data = DepWaitTaskTimes(IN_JSON, time_fields)
    task_data.display_version_slowdown()

if __name__ == '__main__':
    main()
