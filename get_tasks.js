rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
{$match: {version: 'mms_412125d044d0c4f3f80c795d1e173cdc075154b6'}},
{$project: {activated_time:1, activated_by:1, create_time:1, dispatch_time:1, scheduled_time:1, start_time:1, finish_time:1, priority:1, distro:1, depends_on:1, version:1, display_only:1, generated_by:1}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
//{$match: {distro: 'rhel62-small' }},
