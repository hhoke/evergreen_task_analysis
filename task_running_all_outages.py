#!/usr/bin/env python
import datetime, json

import ETA

def active_tasks_during_time(json_fname, time_point):
    """
    active_tasks_during_time takes in a datetime.datetime time point, 
    and a json filename for a json file full of evergreen tasks,
    and returns a set of task display names for tasks active during time_point
    """
    with open(json_fname) as f:
        tasks = json.load(f)

    task_times = {task["display_name"]:(ETA.convert_ISO_to_datetime(task["start_time"]),ETA.convert_ISO_to_datetime(task["finish_time"])) for task in tasks}

    active_tasks = set()
    for name in task_times:
        if task_times[name][0] < time_point and time_point < task_times[name][1]:
            active_tasks.add(name)
        
    return active_tasks

first_event = datetime.datetime(2021, 4, 26, 19, 8, 00, 564000)
second_event = datetime.datetime(2021, 4, 28, 1, 42, 00, 564000)
third_event = datetime.datetime(2021, 4, 29, 2, 49, 00, 564000)
fourth_event = datetime.datetime(2021, 5, 4, 1, 00, 00, 564000)

active_during_first_event = active_tasks_during_time("./firstElectionTasks.json", first_event)
active_during_second_event = active_tasks_during_time("./secondElectionTasks.json", second_event)
active_during_third_event = active_tasks_during_time("./thirdElectionTasks.json", third_event)
active_during_fourth_event = active_tasks_during_time("./fourthElectionTasks.json", fourth_event)

first_two_intersect = active_during_second_event.intersection(active_during_first_event)
all_three_intersect = first_two_intersect.intersection(active_during_third_event)
all_four_intersect = all_three_intersect.intersection(active_during_fourth_event)
print(all_four_intersect)
print(len(all_four_intersect))
