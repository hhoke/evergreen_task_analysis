#!/usr/bin/env python3
'''
plots task waits by finish time. See example_plots/TaskWaitsByFinishTime.html for example of output.
'''
import plotly.express as px                                                                                                     
import ETA

OUT_HTML = './rhel62_08-05-2020_TaskWaitsByFinishTime.html'
IN_JSON = './rhel62_08-05-2020.json'

def timeline_by_finish(df):
    df_sorted = df.sort_values(by=['finish_time'])
    fig = px.timeline(df_sorted, x_start="scheduled_time", x_end="finish_time") 
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

    task_data = ETA.TaskTimes(IN_JSON,time_fields)
    
    fig = timeline_by_finish(task_data.dataframe())
    fig.show()
    fig.write_html(OUT_HTML)
    print('figure saved at {}'.format(OUT_HTML))

if __name__ == '__main__':
    main()
