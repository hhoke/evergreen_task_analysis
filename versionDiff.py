#!/usr/bin/env python3

import datetime  
import json                                                                                                                     
import sys
import ETA

BEGINNING_OF_TIME = datetime.datetime(2000, 1, 1, 0, 0)
# takes in two json with the version name in title
json_one = 'task_json/mms_b501148c740bd81c273af3cb3da11ea2b4da69d9.json'
json_two = 'mms_b2fea32bc34cc0186e3fdd29812aaf6a5b7f7a3a.json'

version_one = 'b501148c740bd81c273af3cb3da11ea2b4da69d9'
version_two = 'b2fea32bc34cc0186e3fdd29812aaf6a5b7f7a3a'

def json_to_set(json_fname, version):
    with open(json_fname) as f:
        j = json.load(f)
    tasks = set()
    for item in j:
        scheduled_time = ETA.convert_ISO_to_datetime(item['scheduled_time'])
        if scheduled_time < BEGINNING_OF_TIME:
            continue
        tasks.add(item['_id'].split(version)[0])
    return tasks

task_set_one = json_to_set(json_one, version_one)
task_set_two = json_to_set(json_two, version_two)

print(task_set_one - task_set_two)
print(task_set_two - task_set_one)
