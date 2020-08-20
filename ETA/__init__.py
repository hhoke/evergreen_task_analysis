#!/usr/bin/env python3
import json                                                                                                                     
import datetime  
import bisect
import pandas as pd                                                                                                             
import numpy as np                                                                                                              

def convert_ISO_to_datetime(time_str):
    '''convert standart ISO time in tasks DB to a datetime.datetime object'''
    try:
        time_object = datetime.datetime.strptime(time_str,'%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        time_object = datetime.datetime.strptime(time_str,'%Y-%m-%dT%H:%M:%SZ')
    return time_object

SHIFT_LATER_FIELD = 'finish_time'
BEGINNING_OF_TIME = datetime.datetime(2000, 1, 1, 0, 0)

class TaskTimes:
    ''' TaskTimes is a container for task dicts with time information.

    Attributes 
    ---
    time_fields: list of strings denoting acceptable time fields that all tasks have

    tasks: {_task_id:task_dict}

    Methods
    ---
    ingest_json: loads json from given filename, returns {_task_id:task_dict}
    
    dataframe: returns pandas dataframe with one task per row and task attributes as columns

    '''

    def __init__(self, in_json, time_fields):
        '''
        TaskTimes is a container for task information, with special handling for datetimes.

        Arguments
        ---
        in_json:
            j = './rhel62_08-05-2020.json'

            Path to a valid json file to be ingested

        time_fields:
            time_fields = [ 'create_time',
                            'scheduled_time',
                            'dispatch_time',
                            'start_time',
                            'finish_time',
                            ]
            Contains the fields to be converted from string to datetime during ingestion
            
        '''
        self.time_fields = time_fields
        self.tasks = self.ingest_json(in_json)

    def ingest_json(self,in_json):

        with open(in_json) as f:
            j = json.load(f)

        tasks = {}
        for item in j:
            _id = item['_id'] 
            tasks[_id] = item
        bad_ids=[]
        for _id in tasks:
            for field in self.time_fields:
                field_string = tasks[_id][field]
                field_ISO = convert_ISO_to_datetime(field_string)
                if field_ISO < BEGINNING_OF_TIME :
                    # bad date, remove
                    bad_ids.append(_id)
                    break
                if SHIFT_LATER_FIELD == field:
                    # add ten seconds to avoid plotly wierdness
                    field_ISO += datetime.timedelta(0,11)
                tasks[_id][field] = field_ISO
        if bad_ids:
            print("bad date, removing:")
        for _id in bad_ids:
            print(tasks[_id])
            del tasks[_id]

        return tasks

    def dataframe(self):
        ''' this enables the return of the self.tasks dict in the form of a pandas 
        dataframe at any point in analysis, after tasks has been modified
        '''
        return pd.DataFrame(list(self.tasks.values()))


# stolen from https://docs.python.org/3/library/bisect.html

def _find_le(a, x):
    'Find rightmost value less than or equal to x'
    i = bisect.bisect_right(a, x)
    if i:
        return a[i-1]
    raise ValueError

def _find_ge(a, x):
    'Find leftmost value greater than or equal to x'
    i = bisect.bisect_left(a, x)
    if i != len(a):
        return a[i]
    raise ValueError
 

class ChunkTimes:
    ''' ChunkTimes automatically creates a list of evenly-spaced datetime.datetime objects, 
        strictly increasing,
        starting with begin_time,
        ending at or after end_time, before end_time + chunk.
        
        Attributes
        ---
        chunk is a datetime.timedelta object
        begin_time and end_time are datetime.datetime objects.
        chunk_list is a list of datetime.datetime objects

        Methods
        ---
        __init__(self, begin_time, end_time, chunk=datetime.timedelta(minutes=5))

            chunk is a datetime.timedelta object
            begin_time and end_time are datetime.datetime objects.
            chunk_list is a list of datetime.datetime objects

            >>> end = datetime.datetime(2000, 1, 1, 0, 0)
            >>> start = datetime.datetime(1999, 12, 31, 16, 0)
            >>> chunk = datetime.timedelta(hours=4)
            >>> willenium = ChunkTimes(start,end,chunk)
            >>> willenium.chunk_list
            [datetime.datetime(1999, 12, 31, 16, 0), datetime.datetime(1999, 12, 31, 20, 0), datetime.datetime(2000, 1, 1, 0, 0)]

        index_tasks_before_chunktime(self, tasks, time_field='finish_time')

            Takes in a list of tasks. 
            Returns chunks dict where tasks are stored under a chunktime fencepost value
            iff they fall before or at the fencepost value, but after the previous fencepost value
            for all time t such that t0 < t <= t1, t is in list d[t1] where d is the returned dictionary
            The time used is specified with the time_field key, 
            as long as the value of that key is a datetime.datetime field in the task.

            all task times must be later than the first fencepost in chunk_list and earlier than the last.

            >>> tasks = [{'finish_time': datetime.datetime(1999, 12, 31, 20, 0)}, 
            ...         {'finish_time': datetime.datetime(1999, 12, 31, 22, 0)},
            ...         {'finish_time': datetime.datetime(1999, 12, 31, 18, 0)}]
            >>> too_early_tasks = [{'finish_time': datetime.datetime(1999, 12, 30, 20, 0)}, 
            ...         {'finish_time': datetime.datetime(1999, 12, 31, 22, 0)},
            ...         {'finish_time': datetime.datetime(1999, 12, 31, 20, 0)}]
            >>> too_late_tasks = [{'finish_time': datetime.datetime(1999, 12, 31, 20, 0)}, 
            ...         {'finish_time': datetime.datetime(1999, 12, 31, 22, 0)},
            ...         {'finish_time': datetime.datetime(2001, 12, 31, 20, 0)}]
            >>> working_chunks = willenium.index_tasks_before_chunktime(tasks)
            >>> for item in working_chunks:
            ...    print(item)
            ...    print(working_chunks[item])
            1999-12-31 16:00:00
            []
            1999-12-31 20:00:00
            [{'finish_time': datetime.datetime(1999, 12, 31, 20, 0)}, {'finish_time': datetime.datetime(1999, 12, 31, 18, 0)}]
            2000-01-01 00:00:00
            [{'finish_time': datetime.datetime(1999, 12, 31, 22, 0)}]
            >>> try: 
            ...    f = willenium.index_tasks_before_chunktime(too_late_tasks)
            ... except ValueError:
            ...     pass
            ... else:
            ...     print('should have failed')
            ...     print(f)

            >>> try: 
            ...    f = willenium.index_tasks_before_chunktime(too_early_tasks)
            ... except ValueError:
            ...     pass
            ... else:
            ...     print('should have failed')
            ...     print(f)

       
        index_tasks_after_chunktime(self, tasks, time_field='finish_time')
            returns chunks dict where tasks are stored under a chunktime fencepost value
            iff they fall at or after the fencepost value, but before the previous fencepost value
            for all time t such that t1 <= t < t2, t is in list d[t1] where d is the returned dictionary.
            The time used is specified with the time_field key, 
            as long as the value of that key is a datetime.datetime field in the task
            >>> working_chunks = willenium.index_tasks_after_chunktime(tasks)
            >>> for item in working_chunks:
            ...    print(item)
            ...    print(working_chunks[item])
            1999-12-31 16:00:00
            [{'finish_time': datetime.datetime(1999, 12, 31, 18, 0)}]
            1999-12-31 20:00:00
            [{'finish_time': datetime.datetime(1999, 12, 31, 20, 0)}, {'finish_time': datetime.datetime(1999, 12, 31, 22, 0)}]
            2000-01-01 00:00:00
            []
            >>> try: 
            ...    f = willenium.index_tasks_after_chunktime(too_early_tasks)
            ... except ValueError:
            ...     pass
            ... else:
            ...     print('should have failed')
            ...     print(f)

            >>> try: 
            ...    f = willenium.index_tasks_after_chunktime(too_late_tasks)
            ... except ValueError:
            ...     pass
            ... else:
            ...     print('should have failed')
            ...     print(f)

        '''

    def __init__(self, begin_time, end_time, chunk=datetime.timedelta(minutes=5)):
        ''' ChunkTimes provides a list of evenly-spaced datetime.datetime objects, 
        strictly increasing,
        starting with begin_time,
        ending at or after end_time, before end_time + chunk.

        chunk is a datetime.timedelta object
        begin_time and end_time are datetime.datetime objects.
        '''
        self.begin_time = begin_time
        self.end_time = end_time
        self.chunk = chunk

        self.chunk_list = []
        current_chunk = begin_time
        while current_chunk < end_time + self.chunk:
            self.chunk_list.append(current_chunk)
            current_chunk += self.chunk 
        # modify end time
        self.end_time = self.chunk_list[-1]

    def index_tasks_before_chunktime(self, tasks, time_field='finish_time'):
        ''' Takes in a list of tasks. 
        Returns chunks dict where tasks are stored under a chunktime fencepost value
        iff they fall before or at the fencepost value, but after the previous fencepost value
        for all time t such that t0 < t <= t1, t is in list d[t1] where d is the returned dictionary.
        The time used is specified with the time_field key, 
        as long as the value of that key is a datetime.datetime field in the task.

        All task times must be later than the first fencepost in chunk_list and earlier than the last.
        '''

        return self._fencepost_assigner_generator(_find_ge)(self, tasks, time_field)

    def index_tasks_after_chunktime(self, tasks, time_field='finish_time'):
        ''' returns chunks dict where tasks are stored under a chunktime fencepost value
        iff they fall at or after the fencepost value, but before the previous fencepost value
        for all time t such that t1 <= t < t2, t is in list d[t1] where d is the returned dictionary.
        The time used is specified with the time_field key, 
        as long as the value of that key is a datetime.datetime field in the task.

        All task times must be later than the first fencepost in chunk_list and earlier than the last.
        '''

        return self._fencepost_assigner_generator(_find_le)(self, tasks, time_field)

    def _fencepost_assigner_generator(self, find_fencepost):
        '''find_fencepost should be a function that takes a list and a value,
        and returns a value from the list. 
        This curries that into a general fencepost assignment function.
        #TODO: remove unneeded closure'''
        def f(self, tasks, time_field):
            fencepost_dict = {x:[] for x in self.chunk_list}
            for task in tasks:
                time_value = task[time_field]
                self._check_in_bounds(time_value)
                fencepost = find_fencepost(self.chunk_list, time_value)
                fencepost_dict[fencepost].append(task)
            return fencepost_dict
        return f

    def _check_in_bounds(self, item):
        ''' checks if an item is between begin_time and end_time.
        item should be a datetime.datetime object'''
        if item < self.begin_time:
            raise ValueError("{} is earlier than begin_time {}".format(item,self.begin_time))
        elif self.end_time < item:
            raise ValueError("{} is later than end_time {}".format(item,self.end_time))

def _test():
    import doctest
    count, _ = doctest.testmod()
    if count == 0:
        print('Doctests passed UwU')
    else:
        print('Doctests failed ;_;')

if __name__ == '__main__':
    _test()
