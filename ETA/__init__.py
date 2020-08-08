import json                                                                                                                     
import datetime  
import pandas as pd                                                                                                             
import numpy as np                                                                                                              

def hist():
    ''' create and save histogram of times'''

def convert_ISO_to_datetime(time_str):
    '''convert standart ISO time in tasks DB to a datetime.datetime object'''
    try:
        time_object = datetime.datetime.strptime(time_str,'%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        time_object = datetime.datetime.strptime(time_str,'%Y-%m-%dT%H:%M:%SZ')
    return time_object

class TaskTimes:
    ''' container for task time information '''

    def __init__(self, in_json, time_fields, shift_later_field):
        self.time_fields = time_fields
        self.shift_later_field = shift_later_field
        self.dataframe = self.ingest_dataframe(in_json)

    def ingest_dataframe(self,in_json):

        with open(in_json) as f:
            j = json.load(f)

        task_dict = {}
        for item in j:
            _id = item['_id'] 
            task_dict[_id] = item
        bad_ids=[]
        for _id in task_dict:
            for field in self.time_fields:
                field_string = task_dict[_id][field]
                field_ISO = convert_ISO_to_datetime(field_string)
                if field_ISO < datetime.datetime(1971, 1, 1, 0, 0):
                    # bad date, remove
                    bad_ids.append(_id)
                    break
                if self.shift_later_field == field:
                    # add ten seconds to avoid plotly wierdness
                    field_ISO += datetime.timedelta(0,11)
                task_dict[_id][field] = field_ISO
        for _id in bad_ids:
            print("removing:")
            print(task_dict[_id])
            del task_dict[_id]

        return pd.DataFrame(list(task_dict.values()))
 

