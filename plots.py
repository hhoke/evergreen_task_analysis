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
OUT_HTML = './rhel76_minHostTest.html'
IN_JSON = './rhel76_minHostTest.json'

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

def generate_twocolor_timeline(df, start='begin_wait', middle='start_time', end='finish_time', sortby='scheduled_time'):

    df = df.sort_values(by=[sortby])
    df_copy = df.copy()
    # create identical copy and introduce color field so you can still group on same y point
    df["color"] = 'Waiting ({} to {})'.format(start,middle)
    df['start'] = df_copy[start]
    df['end'] = df_copy[middle]

    df_copy["color"] = 'Running ({} to {})'.format(middle,end)
    df_copy['start'] = df_copy[middle]
    df_copy['end'] = df_copy[end]

    newdf = pd.concat([df, df_copy]).sort_values(by=[sortby], kind='merge')

    hoverdata = [start, end, 'distro', '_id']
    fig = px.timeline(newdf, x_start='start', x_end='end', color="color", hover_data=hoverdata)
    fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up
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

def generate_hist_raw_wait_time(task_data, additional_filters = None):
    ''' returns histogram of wait times'''
    return generate_hist(task_data, 'raw_wait_time','scheduled_time','start_time', additional_filters = additional_filters)

def generate_hist_corrected_wait_time(task_data, additional_filters = None):
    ''' returns histogram of wait times, corrected for dependencies'''
    return generate_hist(task_data, 'corrected_wait_time','begin_wait','start_time', additional_filters = additional_filters)

def generate_hist_turnaround_time(task_data, additional_filters = None):
    ''' returns histogram of turnaround times'''
    return generate_hist(task_data, 'turnaround_time','scheduled_time','finish_time', additional_filters = additional_filters)

def generate_hist_blocked_time(task_data, additional_filters = None):
    ''' returns histogram of blocked times'''
    return generate_hist(task_data,'blocked_time','scheduled_time','unblocked_time', additional_filters = additional_filters)

def generate_hist(task_data, title, start_key, end_key, additional_filters= None):
    ''' boilerplate function that generates a histogram of some time interval
    from internal task dict.
    task_data is a task times object.
    title is the title of the x axis, must be string
    start_key is the key used to look up the start of the interval for each task
    end_key is analogous
    (value must be datetime.datetime but key is arbitrary)
    additional_filters is a dict of filters to pass to the generator
    e.g. {'distro':['rhel62-small']}
    '''
    finish_times = []
    total = datetime.timedelta(0)
    total_hours = 0
    total_count = 0
    first_time = True
    title = title + '(hours)'
    over_count = 0
    filter_dict = {start_key:[],end_key:[]}
    if additional_filters:
        filter_dict.update(additional_filters)
    for task in task_data.get_tasks(filter_dict):
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

    generator = task_data.get_tasks({'begin_wait':[],'start_time':[],'finish_time':[]})
    task_list = list(generator)
    for task in task_list:
        # have to do this here to avoid polluting the unblock calculations
        # add eleven seconds to avoid plotly wierdness
        task['start_time'] += datetime.timedelta(0,11)
        task['finish_time'] += datetime.timedelta(0,22)


    generator = task_data.get_tasks({'begin_wait':[],'start_time':[],'finish_time':[],'distro':['rhel76-small']})
    df = task_data.dataframe(generator)
    fig = generate_twocolor_timeline(df)
    fig.update_layout(title = 'rhel76_minHostTest')
    fig.show()
    # cdn options reduce the size of the file by a couple of MB.
    out_html = OUT_HTML
    fig.write_html(out_html,include_plotlyjs='cdn',include_mathjax='cdn')
    print('figure saved at {}'.format(out_html))

if __name__ == '__main__':
    main()
