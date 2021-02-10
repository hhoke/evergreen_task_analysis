rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
{$match: {finish_time: {$gt: ISODate("2021-02-09T00:00:00.000Z")}}},
{$match: {finish_time: {$lt: ISODate("2021-02-09T20:20:00.000Z")}}},
{$project: {create_time:1, dispatch_time:1, scheduled_time:1, start_time:1, finish_time:1, distro:1, depends_on:1, display_only:1, generated_by:1, r:1, task_group_max_hosts:1}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
//{$match: {distro: 'rhel62-small' }},
//{$match: {task_group_max_hosts: null }},
