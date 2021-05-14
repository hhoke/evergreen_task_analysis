rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
{$match: {finish_time: {$gt: ISODate("2021-05-04T00:30:00.000Z")}}},
{$match: {finish_time: {$lt: ISODate("2021-05-04T01:30:00.000Z")}}},
{$project: {display_name:1, create_time:1, dispatch_time:1, scheduled_time:1, start_time:1, finish_time:1, priority:1, distro:1, depends_on:1, version:1, display_only:1, generated_by:1, task_group:1}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
//{$match: {distro: 'rhel62-small' }},
