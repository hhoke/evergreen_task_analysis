#!/usr/bin/env python3
'''
plots task waits by finish time.
'''
import datetime
import logging
import plotly.express as px                                                                                                     
import pandas as pd
import ETA
import ETA.Chunks
import DependencyAnalysis

logging.basicConfig(level=logging.INFO)
OUT_HTML = './20201009_MariaReport/foobar.html'
IN_JSON = './foobar.json'


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

def generate_chunked_running_task_count(task_data , chunks):

    tasks = list(task_data.get_tasks({'start_time':[],'finish_time':[]}))
    count_dict = chunks.index_task_on_chunktime_search(tasks)
    count_list = []
    for time in count_dict:
        timepoint_dict = {'time': time, 'active_tasks': count_dict[time] }
        count_list.append(timepoint_dict)

    df = pd.DataFrame(count_list)
    return px.line(df, x="time", y="active_tasks")

def main():
    time_fields = [ 'create_time',
                    'scheduled_time',
                    'start_time',
                    'finish_time',
                    ]

    task_data = DependencyAnalysis.DepWaitTaskTimes(IN_JSON,time_fields)

    for task in task_data.get_tasks():
        # calculate begin_wait and update task with field
        task_data.update_task_unblocked_time(task)

    fig = task_data.generate_hist_corrected_wait_time()
    fig.update_layout(title="foobar")
    fig.show()
    fig.write_html(OUT_HTML)
    print('figure saved at {}'.format(OUT_HTML))



if __name__ == '__main__':
    main()
