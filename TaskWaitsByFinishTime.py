#!/usr/bin/env python3
'''
plots task waits by finish time.
'''
import datetime
import plotly.express as px                                                                                                     
import pandas as pd
import ETA
import ETA.Chunks
import DependencyAnalysis

OUT_HTML = './twocolorsept21rhel62small.html'
IN_JSON = './sept21rhel62small.json'

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
        # calculate begin_wait
        task_data.calculate_task_unblocked_time(task)

    start = datetime.datetime(2020, 9, 21, 0, 0)
    end = datetime.datetime(2020, 9, 22, 0, 0)
    chunk = datetime.timedelta(minutes=5)
    chunks = ETA.Chunks.ChunkTimes(start,end,chunk)
    fig = generate_chunked_running_task_count(task_data, chunks)
    fig.update_layout(title='tasks running per 5min chunk, calculated post-hoc directly from tasks collection')
    fig.show()
    #fig.write_html(OUT_HTML)
    #print('figure saved at {}'.format(OUT_HTML))

if __name__ == '__main__':
    main()
