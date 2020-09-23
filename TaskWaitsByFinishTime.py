#!/usr/bin/env python3
'''
plots task waits by finish time.
'''
import datetime
import plotly.express as px                                                                                                     
import ETA
import DependencyAnalysis

OUT_HTML = './sept21rhel62small.html'
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

    # create identical copy and introduce color field so you can still group on same y point
    df_copy = df
    df["color"] = 1
    df_copy["color"] = 2    

    newdf = df_copy.append(df)
    
    df_sorted = newdf.sort_values(by=[sortby])
    fig = px.timeline(df_sorted, x_start=start, x_end=end, y=sortby, color="color") 
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
    for task in task_data.get_tasks():
        # add eleven seconds to avoid plotly wierdness
        task['start_time'] += datetime.timedelta(0,11)
        task['finish_time'] += datetime.timedelta(0,11)


    df = task_data.dataframe(task_data.get_tasks({'begin_wait':[]}))
    df_sorted = df.sort_values(by=['scheduled_time'])
    fig = generate_timeline(df_sorted, start='begin_wait', end='start_time')
    fig.update_layout(title='begin_wait to start_time, ranked by scheduled_time')
    fig.show()
    fig.write_html(OUT_HTML)
    print('figure saved at {}'.format(OUT_HTML))

if __name__ == '__main__':
    main()
