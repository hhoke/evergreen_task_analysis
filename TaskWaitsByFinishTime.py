#!/usr/bin/env python3
'''
plots task waits by finish time.
'''
import datetime
import plotly.express as px                                                                                                     
import ETA
import DependencyAnalysis

OUT_HTML = './burstyPerf.html'
IN_JSON = './burstyPerf.json'

def generate_timeline_by_endtime(df, start='scheduled_time', end='finish_time'):
    df_sorted = df.sort_values(by=[end])
    fig = px.timeline(df_sorted, x_start=start, x_end=end) 
    fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up 
    fig.update_layout({
    'plot_bgcolor': 'rgba(0, 0, 0, 0)',
    'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    })
    return fig

def main():
    time_fields = [ 'create_time',
                    'scheduled_time',
                    'dispatch_time',
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
        task['finish_time'] += datetime.timedelta(0,11)

    generator = task_data.get_tasks({'finish_time':[],'scheduled_time':[]})
    fig = generate_timeline_by_endtime(task_data.dataframe(generator),start='scheduled_time')
    fig.show()
    fig.write_html(OUT_HTML)
    print('figure saved at {}'.format(OUT_HTML))

if __name__ == '__main__':
    main()
