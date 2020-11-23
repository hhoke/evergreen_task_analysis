#!/usr/bin/env python3
''' versionDiff.py determines which task types are in one version but not the other,
after ingesting a specified json for each version.'''

import datetime  
import json                                                                                                                     
import sys
import ETA

BEGINNING_OF_TIME = datetime.datetime(2000, 1, 1, 0, 0)
# takes in two json with the version name in title
json_one = 'mms_412125d044d0c4f3f80c795d1e173cdc075154b6.json'
json_two = 'mms_40262a6015110e6b076c6d6f5b45368f32758276.json'

version_one = '412125d044d0c4f3f80c795d1e173cdc075154b6'
version_two = '40262a6015110e6b076c6d6f5b45368f32758276'

def json_to_set(json_fname, version):
    with open(json_fname) as f:
        j = json.load(f)
    tasks = set()
    for item in j:
        scheduled_time = ETA.convert_ISO_to_datetime(item['scheduled_time'])
        if scheduled_time < BEGINNING_OF_TIME:
            continue
        if item['distro'] != 'rhel76-small':
            continue
        tasks.add(item['_id'].split(version)[0])
    return tasks

task_set_one = json_to_set(json_one, version_one)
task_set_two = json_to_set(json_two, version_two)

print(task_set_one - task_set_two)
print(task_set_two - task_set_one)
