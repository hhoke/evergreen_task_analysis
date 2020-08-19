#!/usr/bin/env python
'''
analysis of task dependencies
'''
import ETA
import datetime

OUT_HTML = './rhel62_08-05-2020_TaskWaitsByFinishTime.html'
IN_JSON = './rhel62_08-05-2020.json'
DISTROS = ['rhel62-large']

class DepTaskTimes(ETA.TaskTimes):
    '''
    DepTaskTimes extends ETA.TaskTimes. It adds distro-filtering functionality,
    along with advanced dependency-crawling functionality.
    '''

    def __init__(self, in_json, time_fields):
        '''
        DepTaskTimes extends ETA.TaskTimes. It adds distro-filtering functionality,
        along with advanced dependency-crawling functionality.
        '''
        # due to the added functionality, 
        # this class requires a lot of different time fields.
        required_fields = [ 'create_time',
                            'scheduled_time',
                            'start_time',
                            'finish_time',
                            ]
        required_fields_missing = []
        for field in required_fields:
            if field not in time_fields:
                required_fields_missing.append(field)
        if required_fields_missing:
            raise ValueError("required fields missing: {}".format(required_fields_missing))

        super().__init__(in_json,time_fields)
    

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
                 
    def screen_task_by_distros(self, distros):
        ''' screen tasks by distros, screen out tasks with broken/nonexistent dependency info
        returns distro_tasks, which is a dict of lists of tasks in the distro

        distro:
            d = ['rhel62-large']
            Used to filter out "protagonist" tasks from a larger dump of tasks from all distros.
            This is useful when you only care about wait times for a couple of distros, but they
            have dependencies from multiple distros.

        '''
        distro_tasks = {x:[] for x in distros}
        for _id in self.tasks:
            task = self.tasks[_id]
            if task['distro'] in distros:
               distro_tasks[task['distro']].append(task)
        return distro_tasks

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

    @staticmethod 
    def calculate_latency_slowdown(task): 
        ''' adds 'latency_slowdown' field to task '''

        proportion_of_ideal = (task['finish_time'] - task['create_time']) / task['perfect_world_latency']
        if proportion_of_ideal > 0:
            task['latency_slowdown'] = proportion_of_ideal
        else:
            task['latency_slowdown'] = np.nan
 
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

def sample_trees():
    '''stub (min, max, 10%ile, 90th%ile, mean) displays 1 tree for each in a color-coded gantt chart'''
    pass

def hist_total_wait_times():
    ''' stub ''' 
    pass


def main():
    time_fields = [ 'create_time',
                    'scheduled_time',
                    'dispatch_time',
                    'start_time',
                    'finish_time',
                    ]

    task_data = DepTaskTimes(IN_JSON, time_fields)
    task_data.wait_blocked_totals()

if __name__ == '__main__':
    main()
