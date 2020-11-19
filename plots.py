#!/usr/bin/env python3
'''
plots task waits by finish time, and other plots.
'''
import datetime
import logging
import plotly.express as px
import pandas as pd

import ETA.Chunks as chunks
import metrics

logging.basicConfig(level=logging.INFO)
#OUT_HTML = './foobar.html'
IN_JSON = './cruisin.json'

##
# gantt
def generate_timeline(df, start='scheduled_time', end='finish_time', y=None):
    if not y:
        fig = px.timeline(df, x_start=start, x_end=end)
    else:
        fig = px.timeline(df, x_start=start, x_end=end, y=y)
    fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up
    fig.update_layout({
    'plot_bgcolor': 'rgba(0, 0, 0, 0)',
    'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    })
    return fig

def generate_twocolor_timeline(df, start='begin_wait', middle='start_time', end='finish_time', sortby='scheduled_time', 
        highlighted_tasks=None):

    df = df.sort_values(by=[sortby])
    df_copy = df.copy()
    # create identical copy and introduce color field so you can still group on same y point
    df['color'] = 'Waiting ({} to {})'.format(start,middle)
    df['start'] = df_copy[start]
    df['end'] = df_copy[middle]

    df_copy['color'] = 'Running ({} to {})'.format(middle,end)
    df_copy['start'] = df_copy[middle]
    df_copy['end'] = df_copy[end]

    newdf = pd.concat([df, df_copy]).sort_values(by=[sortby], kind='merge')

    if highlighted_tasks:
        for task_id in highlighted_tasks:
            newdf.loc[newdf._id == task_id, 'color'] = "highlighted"

    hoverdata = [start, end, 'distro', '_id']
    fig = px.timeline(newdf, x_start='start', x_end='end', color="color", hover_data=hoverdata)
    fig.update_yaxes(autorange='reversed') # otherwise tasks are listed from the bottom up
    fig.update_layout({
    'plot_bgcolor': 'rgba(0, 0, 0, 0)',
    'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    })
    return fig

##
# line

def generate_chunked_running_task_count(task_list, chunk_times):
    ''' task data must be an ETA.TaskTimes object.
    this creates a basic line chart of tasks running per time
    using ETA.Chunks.
    '''

    count_dict = chunk_times.index_task_on_chunktime_search(task_list)
    count_list = []
    for time in count_dict:
        timepoint_dict = {'time': time, 'active_tasks': count_dict[time] }
        count_list.append(timepoint_dict)

    df = pd.DataFrame(count_list)
    return px.line(df, x="time", y="active_tasks")

##
# histogram

def generate_hist_raw_wait_time(task_data):
    ''' returns histogram of wait times'''
    return generate_hist(task_data, 'raw_wait_time','scheduled_time','start_time')

def generate_hist_corrected_wait_time(task_data):
    ''' returns histogram of wait times, corrected for dependencies'''
    return generate_hist(task_data, 'corrected_wait_time','begin_wait','start_time')

def generate_hist_turnaround_time(task_data):
    ''' returns histogram of turnaround times'''
    return generate_hist(task_data, 'turnaround_time','scheduled_time','finish_time')

def generate_hist_blocked_time(task_data):
    ''' returns histogram of blocked times'''
    return generate_hist(task_data,'blocked_time','scheduled_time','unblocked_time')

def generate_hist(task_data, title, start_key, end_key):
    ''' boilerplate function that generates a histogram of some time interval
    from internal task dict.
    title is the title of the x axis, must be string
    start_key is the key used to look up the start of the interval for each task
    end_key is analogous
    (value must be datetime.datetime but key is arbitrary)
    '''
    finish_times = []
    total = datetime.timedelta(0)
    total_hours = 0
    total_count = 0
    first_time = True
    title = title + '(hours)'
    over_count = 0
    for task in task_data.get_tasks({start_key:[],end_key:[]}):
        time_delta = task[end_key] - task[start_key]
        seconds_in_minute = 60
        minutes_in_hour = 60
        time_delta_hour = (time_delta.seconds / seconds_in_minute) / minutes_in_hour
        finish_times.append({title:time_delta_hour})
        total_hours += time_delta_hour
        total += time_delta
        total_count += 1
        if time_delta_hour >= 1:
            logging.info(task["_id"])
            logging.info(task["version"])
            over_count +=1
        if first_time:
            worst = {time_delta_hour:task}
            first_time = False
        if time_delta_hour > next(iter(worst)):
            worst = {time_delta_hour:task}
    df = pd.DataFrame(finish_times)
    fig = px.histogram(df, x=title)
    logging.info(total_hours/total_count)
    logging.info(over_count)
    return fig

def main():
    time_fields = [ 'create_time',
                    'scheduled_time',
                    'start_time',
                    'finish_time',
                    ]

    task_data = metrics.DepWaitTaskTimes(IN_JSON,time_fields)
    start = datetime.datetime(2020, 10, 14, 12, 0)
    end = datetime.datetime(2020, 10, 15, 8, 0)
    chunk = datetime.timedelta(minutes=5)
    chunk_times = chunks.ChunkTimes(start, end, chunk)
    generator = task_data.get_tasks({'begin_wait':[],'start_time':[],'finish_time':[]})
    task_list = list(generator)
    task_list = [task for task in task_list if task['wait_time'] > datetime.timedelta(hours=1)]
    versions = []
    vorsions = {}
    for task in task_list:
        if task['version'] not in versions:
            versions.append(task['version'])
            vorsions[task['version']] = [task['_id']]
        else: 
            vorsions[task['version']].append(task['_id'])

    print(vorsions)
    print(len(task_list))

    generator = task_data.get_tasks({'begin_wait':[],'start_time':[],'finish_time':[]})
    task_list = list(generator)
    for task in task_list:
    # have to do this here to avoid polluting the unblock calculations
        # add eleven seconds to avoid plotly wierdness
        task['start_time'] += datetime.timedelta(0,11)
        task['finish_time'] += datetime.timedelta(0,22)
   
    print(len(versions))
    slowdowns_by_version = {}
    for version in versions:
    
        generator = task_data.get_tasks({'begin_wait':[],'start_time':[],'finish_time':[],'version':[version]})
        version_tasks = {task['_id']:task for task in generator}
        if len(version_tasks) < 100:
            continue

        try:
            slowdown, _  = metrics.DepGraph.display_version_slowdown(version_tasks)
            slowdowns_by_version[version] = slowdown
        except ValueError as e:
            print(e)
            continue
        generator = task_data.get_tasks({'begin_wait':[],'start_time':[],'finish_time':[],'version':[version]})
        df = task_data.dataframe(generator)
        
        naughty_tasks_ids = vorsions[version]
        highlighted_tasks = []
        for task_id in naughty_tasks_ids:
            distro = version_tasks[task_id]['distro']
            bad_distros = ['power8','zseries','macos','windows','perf']
            #bad_distros=[]
            bad_distro = False
            for bad in bad_distros:
                if bad in distro:
                    bad_distro = True
            if bad_distro:
                continue
            else:
                highlighted_tasks.append(task_id)
        print()
        print(highlighted_tasks)
        print()
        fig = generate_twocolor_timeline(df,highlighted_tasks=highlighted_tasks)
        fig.update_layout(title = version)
        fig.show()
        # cdn options reduce the size of the file by a couple of MB.
        out_html = './{}.html'.format(version)
        fig.write_html(out_html,include_plotlyjs='cdn',include_mathjax='cdn')
        print('figure saved at {}'.format(out_html))

    sorted_slowdowns_by_version  = dict(sorted(slowdowns_by_version.items(), key=lambda item: item[1]))
    for version in sorted_slowdowns_by_version:
        print('{}: {}'.format(sorted_slowdowns_by_version[version],version))

if __name__ == '__main__':
    main()
