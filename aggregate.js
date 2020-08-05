DBQuery.shellBatchSize = 330555;
rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
{$match: {finish_time: {$gt: ISODate("2020-08-04T12:00:00.000Z")}}},
{$match: {finish_time: {$lt: ISODate("2020-08-05T12:00:00.000Z")}}},
{$match: {distro: 'rhel62-large'}},
{$project: {create_time:1, dispatch_time:1, scheduled_time:1, start_time:1, finish_time:1, priority:1, distro:1, depends_on:1}},
])};
var x = problemChild().toArray();
printjson(x)
