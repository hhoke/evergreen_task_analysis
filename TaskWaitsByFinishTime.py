#!/usr/bin/env python3
'''
plots task waits by finish time.
'''
import datetime
import plotly.express as px                                                                                                     
import pandas as pd
import ETA
import DependencyAnalysis

OUT_HTML = './twocolorsept21rhel62small.html'
IN_JSON = './sept21rhel62small.json'

def generate_timeline(df, start='scheduled_time', end='finish_time'):
    fig = px.timeline(df, x_start=start, x_end=end) 
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
    df["color"] = 'Waiting'
    df.rename(columns = {start:'start'}, inplace = True)
    df.rename(columns = {middle:'end'}, inplace = True)

    df_copy["color"] = 'Running'   
    df_copy.rename(columns = {middle:'start'}, inplace = True)
    df_copy.rename(columns = {end:'end'}, inplace = True)

    newdf = pd.concat([df, df_copy]).sort_index(kind='merge')
   
    df_sorted = newdf 
    print(df_sorted)
    fig = px.timeline(df_sorted, x_start='start', x_end='end', color="color") 
    fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up 
    fig.update_layout({
    'plot_bgcolor': 'rgba(0, 0, 0, 0)',
    'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    })
    return fig

def generate_timeline_by_host(df, start='start_time', end='finish_time'):
    fig = px.timeline(df, x_start=start, x_end=end, y="host_id") 
    fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up 
    fig.update_layout({
    'plot_bgcolor': 'rgba(0, 0, 0, 0)',
    'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    })
    return fig


def main():
    time_fields = [ 'create_time',
                    'scheduled_time',
                    'start_time',
                    'finish_time',
                    ]

    task_data = DependencyAnalysis.DepWaitTaskTimes(IN_JSON,time_fields)
    for task in task_data.get_tasks():
        # calculate begin_wait
        task_data.calculate_task_unblocked_time(task)

    # have to do this as a second loop to avoid pollutint the unblock calculations
    generator = task_data.get_tasks({'begin_wait':[],'start_time':[],'finish_time':[]})
    for task in generator:
        # add eleven seconds to avoid plotly wierdness
        task['start_time'] += datetime.timedelta(0,11)
        task['finish_time'] += datetime.timedelta(0,22)


    generator = task_data.get_tasks({'begin_wait':[],'start_time':[],'finish_time':[]})
    df = task_data.dataframe(generator)
    fig = generate_twocolor_timeline(df)
    fig.update_layout(title='begin_wait to start_time, ranked by scheduled_time')
    fig.show()
    #fig.write_html(OUT_HTML)
    #print('figure saved at {}'.format(OUT_HTML))

if __name__ == '__main__':
    main()
