#!/usr/bin/env python3

import datetime  
import json                                                                                                                     
import logging
import pandas as pd                                                                                                             

def convert_ISO_to_datetime(time_str):
    '''convert standart ISO time in tasks DB to a datetime.datetime object'''
    try:
        time_object = datetime.datetime.strptime(time_str,'%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        time_object = datetime.datetime.strptime(time_str,'%Y-%m-%dT%H:%M:%SZ')
    return time_object

BEGINNING_OF_TIME = datetime.datetime(2000, 1, 1, 0, 0)

class TaskTimes:
    ''' TaskTimes is a container for task dicts with time information.

    Attributes 
    ---
    time_fields: list of strings denoting acceptable time fields that all tasks have

    tasks: {_task_id:task_dict}
    
    screen_by: modifier for the central tasks iterator. Default is none, should be set to a dict.
        TaskTime.get_tasks()  will screen out all tasks without the fields in screen_by.keys().
        If the value of a key in screen_by is empty, all field values are allowed in tasks.
        If this value is set to a list, only tasks with field values matching the list will be returned.

    Methods
    ---
    ingest_json: loads json from given filename, returns {_task_id:task_dict}
    
    dataframe: returns pandas dataframe with one task per row and task attributes as columns


    >>> time_fields = ['create_time',
    ...                 'scheduled_time',
    ...                 'dispatch_time',
    ...                 'start_time',
    ...                 'finish_time',
    ...                 ]
    >>> TT = TaskTimes('./shorty.json', time_fields)
    >>> for task in TT.get_tasks():
    ...     print(task['_id'])
    compile
    1
    2
    3
    >>> bins = TT.bin_tasks_by_field('distro')
    >>> for b in bins:
    ...     print('{}: {}'.format(b, [x['_id'] for x in bins[b]])) 
    rhel62-large: ['compile', '2', '3']
    rhel62-small: ['1']
    >>> TT.screen_by = {'distro': ['rhel62-small']} 
    >>> for task in TT.get_tasks():
    ...     print(task['_id'])
    1
    >>> bins = TT.bin_tasks_by_field('distro')
    >>> for b in bins:
    ...     print('{}: {}'.format(b, [x['_id'] for x in bins[b]])) 
    rhel62-small: ['1']
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
            Contains the fields to be converted from string to datetime during ingestion
            TODO: include some kind of schema validation for fields like 'depends_on'
            https://www.peterbe.com/plog/jsonschema-validate-10x-faster-in-python
        screen_by: modifier for the central tasks iterator.
            
        '''
        self.time_fields = time_fields
        self.tasks = self.ingest_json(in_json)
        self.screen_by = None

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
                tasks[_id][field] = field_ISO
        if bad_ids:
            logging.debug("bad date, removing:")
        for _id in bad_ids:
            logging.debug(tasks[_id])
            del tasks[_id]

        return tasks

    def dataframe(self, task_generator=None):
        ''' this enables the return of the self.tasks dict in the form of a pandas 
        dataframe at any point in analysis, after tasks has been modified
        '''
        if not task_generator:
            task_generator = self.get_tasks()
        screened_tasks = list(task_generator)
        return pd.DataFrame(screened_tasks)
    
    def get_tasks(self, adhoc_screen=None, mode='polite_merge'):
        ''' generator that returns tasks according to self.screen_by attribute of the form {str:[]}.
        get_tasks()  will screen out all tasks without the fields in screen_by.keys().
        If the value of a key in screen_by is empty, all field values are allowed in tasks.
        If this value is set to a list, only tasks with field values matching the list will be returned.

        screen_modes:
        'substitute': adhoc_screen temporarily overrides default screen_by completely
        'polite_merge': adhoc_screen is added to default screen_by. 
            For colliding keys, default takes precedence.
        'merge': adhoc_screen is added to default screen_by.
            For colliding keys, adhoc_screen takes precedence.
        '''
        if mode == 'polite_merge':
            if adhoc_screen and self.screen_by:
                screen = { **adhoc_screen, **self.screen_by } 
            elif adhoc_screen:
                screen = adhoc_screen
            else:
                screen = self.screen_by
        elif mode == 'merge':
            if adhoc_screen and self.screen_by:
                screen = { **self.screen_by, **adhoc_screen} 
            elif adhoc_screen:
                screen = adhoc_screen
            else:
                screen = self.screen_by
        elif mode == 'substitute':
            if adhoc_screen:
                screen = adhoc_screen  
            else:
                screen = self.screen_by
        else:
            raise ValueError('unknown mode {}, allowed values are "merge", "polite_merge", "substitute"'.format(mode))
        returned_none = True
        for _id in self.tasks:
            task = self.tasks[_id] 
            invalid_field = False
            if screen:
                for field in screen:
                    if field not in task:
                        invalid_field = True
                        break
                    elif screen[field]:
                        if task[field] not in screen[field]:
                            invalid_field = True
                            break
            if not invalid_field:
                if returned_none:
                    returned_none = False
                yield task
        if returned_none:
            logging.warning('Returned no task values for screen')
            logging.warning(screen)
            logging.warning('sample task')
            logging.warning(task)

    def bin_tasks_by_field(self, field, values=None, task_generator=None):
        ''' instead of simply filtering tasks using a built in screen_by, 
        returns tasks binned by allowed values of a given field.'''
        if not task_generator:
            task_generator = self.get_tasks()
        tasks = {}
        if values:  
            tasks = {x:[] for x in values}
        for task in task_generator:
            if values:
                if task[field] in values:
                   tasks[task[field]].append(task)
            else:
                if task[field] in tasks:
                   tasks[task[field]].append(task)
                else:
                   tasks[task[field]] = [task]
        return tasks

def _test():
    import doctest
    count, _ = doctest.testmod()
    if count == 0:
        print('Doctests passed UwU')
    else:
        print('Doctests failed ;_;')
        print('did you \'member to run from top level project dir?')

if __name__ == '__main__':
    _test()
