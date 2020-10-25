# Evergreen Performance Guide

Evergreen runs over 100,000 tasks per day. We aggregate task data in many ways -- by aggregating task statistics directly, or by constructing statistics based on the structure of versions (patch or waterfall). Similarly, we can break down summary statistics by distro, distro state, time of day, task priority, and so on. In order to get a representative picture of evergreen performance, we're going to have to look at vignettes from multiple scales and vantage points.

## Metrics

### Aggregate Task Statistics

Aggregate task statistics can be especially useful when comparing the performance of distros.

#### Naive Task Wait

We can easily visualize task wait in splunk in a variety of ways, as with the following query:
[index=evergreen stat=task-end-stats distro=rhel76-small | eval hours = (total_wait_secs / 60 ) / 60 | timechart span=5m max(hours) avg(hours)](https://mongodb.splunkcloud.com/en-US/app/search/search?earliest=1603026000&latest=1603112400&sid=_aGFycmlzLmhva2U_aGFycmlzLmhva2U__search__search6_1603302737.252704&q=search%20index%3Devergreen%20stat%3Dtask-end-stats%20distro%3Drhel76-small%20%7C%20eval%20hours%20%3D%20(total_wait_secs%20%2F%2060%20)%20%2F%2060%20%7C%20timechart%20span%3D5m%20max(hours)%20avg(hours)&display.page.search.mode=fast&dispatch.sample_ratio=1&display.general.type=statistics)

The metric that is used in the splunk link is defined something like this:
```
total_wait_secs := start_time - scheduled_time 
```
However, there is a problem: this may include time where a task was blocked by dependencies.
Even in the best scheduling system, tasks will still have to wait until their dependencies finish. 
So, I almost never use this, as it is an over-estimate of task wait time.

#### Corrected Task Wait

There is an obvious correction to the above problem: use `unblocked_time` instead of `scheduled_time`:
```
unblocked_time := max(dependency_finish_times)
begin_wait := max(scheduled_time, unblocked_time)
wait_time := start_time - begin_wait
```
However, this has its own problem: when a task has been sitting in the queue while blocked, this may cause it to be weighted higher and therefore run faster than if it had been submitted without dependencies at `unblocked_time`. 
As such, this may be a slight under-estimate of task wait time. 
However, we can be sure it is not an over-estimate.
This is currently what I use to evaluate task and distro performance, so much so that I have begun to refer to it as `wait_time` and the naive approach as `uncorrected_wait_time`.
This metric also has the bonus of decoupling distro performance from one another. To clarify, often a performant distro such as rhel62-small will have tasks that depend on tasks from poorly-performing distros such as rhel67-zseries-large. This situation would no longer affect rhel62-small if we take the `unblocked_time` into consideration.

(Note: at one point `unblocked_time` was computed in evergreen, however this created performance problems and the functionality was removed)

Corrected task wait is calculated automatically by the core task data ingestion engine used by both `metrics.py` and `plots.py`, and stored under the `begin_wait` field in each task dictionary.

#### Lies, Damn Lies, and Task Summary Statistics 

Averages are one of the first summary statistics people think to use when comparing groups.
However, consider the following contrived patch builds:

turnaround times for **Solid Build**

`compile`: 3 minutes  
`smokeTest`: 3 minutes  
... 97 other tests, all miraculously completing in 3 minutes each  
`cleanUp`: 3 minutes  

The average time here is clearly 3 minutes.

turnaround times for **Punished Build**

`compile`: 100 minutes  
`smokeTest`: 3 minutes  
... 97 other tests, even more miraculously completing in 2 minutes each  
`cleanUp`: 3 minutes  

The average time here is clearly 3 minutes as well. 

Still, the impact on turnaround time for the entire patch build is drastic.
Assume at least one task depends on `compile`, but there are no other dependencies.

**Solid Build** has a version turnaround time of 6 minutes.  
**Punished Build** has a version turnaround time of 103 minutes.

You could also imagine an alternate scenario where **Punished Build** had a _lower_ average, but still had a much worse turnaround time.

If you think through the above two examples, you can see that for certain dependency structures, this can affect metrics both corrected for dependency blocking and uncorrected.

In many fields, outliers are to be ignored. However, the above example illustrates how important outlying values are when it comes to version performance.

Current best practice is to compare distros by calculating the percentage of tasks that have a wait time greater than 10 minutes. This fails to capture the severity of outliers, but is a decent approximation of how often long wait events occur.

### Version Statistics

While people may care a lot about the wait time for particular tasks, in general evergreen users care most about how long it takes for a patch or mainline commit to finish. The best metric I have found for this so far is slowdown.

### Slowdown 

Slowdown is an accepted metric defined loosely as the proportion of the ideal time it takes something to run, or alternatively, turnaround time on a system under heavy load divided by turnaround time on a system under light load<a id="slowdowndefinition">[\[Slowdown Definition\]](#Slowdown-Definition)</a>. 
For single tasks, there are well known issues caused by task variability. 
For example, a task that takes a second to run would have an idealized turnaround time of 1 second, and a slowdown of 10 in the case where it takes 10 seconds to schedule. 
However, in practice this performance is completely acceptable. 

Version structure allows us to sidestep a lot of the problems with high levels of task variability, because it it is large relative to the kinds of delays we usually see for tasks. Additionally, it allows us to sidestep a lot of the issues surrounding task averages, and to compute a metric that directly evaluates version turnaround time itself.

#### Constructing a Slowdown Metric for Evergreen

It is well known that a DAG of tasks can run no faster than the <a id="criticalpath">[\[Critical Path\]](#Critical-Path)</a>.
This is defined as the dependency chain that takes the greatest amount of time to complete.
We can use this to model the idealized turnaround time of a given version task DAG.

To elide implementation details, we remove display tasks from the task DAG and then find the critical path.
Our ideal runtime is the total time it would take to run this critical path assuming infinite parallel capacity and instantaneous scheduling.
That is, the idealized turnaround time is the sum of all critical path tasks' run times. 

The actual turnaround time is calculated as the total turnaround time for the entire patch build, minus any time where no task was running or scheduled (This helps to account for tasks scheduled after-the-fact, though it's not perfect).

This metric is particularly useful for finding examples of very poor performance. You can rank versions in a given time period (or any dataset, really) using `DepWaitTaskTimes.display_slowdown_by_version()` in `metrics.py`.
I'm working on making this a more useful tool for comparison and evaluation. Right now if a build scores well on this metric, I can be confident it is in fact performing well. I can be confident that if a version performs poorly, its performance is indeed poor.

However, I have not built up enough experience working with this metric, and refined the metric enough, to understand 

1) If I am accounting for manually-scheduled reruns (I think I still need to figure this out)
2) The effect of individual tasks on version performance (though I'm getting there)
3) How accurate relative comparisons of versions are when the slowdown number is in the same ballpark

## Visualizations

### splunk dashboards

I use the [Burst Stats Dashboard](https://mongodb.splunkcloud.com/en-US/app/search/burst_stats?form.distro=rhel76-small&form.time.earliest=1603026000&form.time.latest=1603112400) to investigate poorly-performing distros, ususally on the scale of around a day. The top of the board gives you information about host creation dynamics, while the middle of the board contains information about tasks and task queues. The bottom of the board contains potential causes of poor performance.

### plots
These plots can all be generated using `plots.py`.

#### Histograms

<iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="https://evergreen-task-analysis.s3.us-east-2.amazonaws.com/windows-64-vs2019-large.html" height="525" width="100%"></iframe>

This is a sample histogram of a windows distro, in which we can see its characteristically bad performance.

## Performance Case Studies

### Global Performance

#### Redlining

What does Evergreen look like when you test its limits?

August 6th and 7th, 2020, we raised most of the distro-specific limits to allow the most in-demand distros to freely provision hosts. Total hosts increased to over 6000. 

The most immediate limit to evergreen task processing volume is logkeeper. At roughly 5000 total dynamic hosts, logkeeper began to produce more errors. These include serious errors like `Bad request to appendGlobalLog: unexpected EOF`. Some logs fail to make it to logkeeper, though most are fine.

At just over 6000 hosts, we got the following error from AWS:

```
"You have exceeded your maximum gp2 storage limit of 1746 TiB in this region. Please contact AWS Support to request an Elastic Block Store service limit increase."
```
As the message says, this is a soft limit that can be increased simply by contacting AWS support.

The load on logkeeper and the amount of EBS storage used clearly depends on the particular jobs and distros running. However, we now have rough estimates on the limits of scaling and have instituted rough checks to protect evergreen from becoming unstable as the number of hosts becomes too large. 

Currently, max total dynamic hosts is set at 5000, in order to prevent logkeeper errors. Logkeeper is slowly being phased out. Once it is completely removed, we plan to conduct further tests to understand the particular settings and conditions that constrain Evergreen scaling. We expect to be able to easily scale past 6000 hosts, but have yet to identify the next set of constraints.

### Distro Performance 

#### Driving in first gear

If Evergreen was a car, this case would analogous to driving it in first gear on the interstate.

This is a gantt chart of all tasks from rhel62-large from UTC noon, August 4th, 2020, to UTC 8AM, August 5th.
This and all other gantt charts consist of tasks ordered from top to bottom by `scheduled_time`. There are two bars per task, as described below in the <a id="gantt-intro">[\[Glossary\]](#Glossary)</a>, but they are not visile as distinct bars in this image due to the number of tasks.

The frame below is not interactive, due to its size. 
<iframe id="Totaled" scrolling="no" style="border:none;" seamless="seamless" src="https://evergreen-task-analysis.s3.us-east-2.amazonaws.com/totaled.png" height="944" width="630" style="-webkit-transform:scale(0.5);-moz-transform-scale(0.5);"></iframe>

As you can see above, 2,970 tasks waited for greater than eight hourse before they began. The above figure somewhat overstates this, due to visualization artefacts caused by the number of tasks.

The average wait time for this period was roughly 39 minutes, with 19,714 tasks waiting for more than an hour, about 14.6% of the total.

You can look at the relevant [burst stats dash output](https://evergreen-task-analysis.s3.us-east-2.amazonaws.com/rhel62-Aug42020-maxhosts.pdf)

The cause of this issue is that the distro hit the max hosts cap for that distro. As soon as this occured, evergreen was unable to scale hosts to meet demand and some tasks were left to languish in the queue for many hours until the backlog was cleared. As a consequence of this investigation, we now try to avoid using a distro-specific max hosts cap.

See tickets [EVG-12744](https://jira.mongodb.org/browse/EVG-12744) and [EVG-12887](https://jira.mongodb.org/browse/EVG-12887).

#### Don't Fear the Reaper

This case documents a time when AWS terminated an unusually high number of spot instances early.

For ease of comparison, these data consist of all tasks from rhel62-large from UTC noon, September 8th, 2020, to UTC 8AM, September 9th. The load at this time was much reduced, with around 35% of the total task volume for the period shown above.

<iframe id="reapin" scrolling="no" style="border:none;" seamless="seamless" src="https://evergreen-task-analysis.s3.us-east-2.amazonaws.com/reapin.html" height="525" width="100%"></iframe>

As you can see, zero tasks waited for greater than eight hours.

The average wait time for this period was roughly 13 and a half minutes, with 2,138 tasks waiting for more than an hour, about 4.6% of the total.

You can look at the relevant [burst stats dash output](https://evergreen-task-analysis.s3.us-east-2.amazonaws.com/rhel62-Sept82020-ec2reap.pdf)

Note the choppy pattern in the host count caused by these intermittent reapings. It takes time to recover by allocating and provisioning new hosts, and performance is affected, but not nearly as badly as when a host cap is reached.

#### Cruisin'

A snapshot of evergreen doing what it was made to do, with everything running smoothly. 

For ease of comparison, these data consist of all tasks from rhel62-large from UTC noon, October 14th, 2020, to UTC 8AM, October 15th. The load was actually a bit greater than the reaping example shown above, but there were no exceptional circumstances that might degrade performance.

<iframe id="cruisin" scrolling="no" style="border:none;" seamless="seamless" src="https://evergreen-task-analysis.s3.us-east-2.amazonaws.com/cruisin.html" height="525" width="100%"></iframe>

<iframe id="cruisin-hist" scrolling="no" style="border:none;" seamless="seamless" src="https://evergreen-task-analysis.s3.us-east-2.amazonaws.com/cruisin_hist.html" height="525" width="100%"></iframe>


The average wait time for this period was roughly four and a half minutes, with 193 tasks waiting for more than an hour, about 0.3% of the total. Things are largely functioning as they should, although this long tail of 193 tasks is worrying.

[burst stats dash output]("https://evergreen-task-analysis.s3.us-east-2.amazonaws.com/rhel62-Oct142020-cruisin.pdf")

It is still an open question [why this long tail exists](https://jira.mongodb.org/browse/EVG-13058).

However, we can investigate the impact of some of these jobs on their versions using the slowdown metric discussed above.

### Version Performance

TODO, I need a better handle on interpreting the effect of particular tasks on the slowdown metric.

Glossary
--- 

**Version**: patch build or mainline commit build / waterfall
<iframe id="Task-Terms" scrolling="no" style="border:none;" seamless="seamless" src="https://evergreen-task-analysis.s3.us-east-2.amazonaws.com/task-intervals.svg" height="525" width="100%"></iframe>

<b id="Glossary"></b>Return to Case Studies[↩](#gantt-intro)

Citations
---

<b id="Slowdown-Definition"></b>https://www.cs.huji.ac.il/~feit/parsched/jsspp98/p-98-1.pdf[↩](#slowdowndefinition)

<b id="Critical-Path"></b>https://arxiv.org/pdf/1701.08800.pdf[↩](#criticalpath)
