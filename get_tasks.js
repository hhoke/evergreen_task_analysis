rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
{$match: {version: "mms_170e5b497576b20b118c4befbaf83696f894a7dc"}},
{$project: {create_time:1, dispatch_time:1, scheduled_time:1, start_time:1, finish_time:1, priority:1, distro:1, depends_on:1, version:1}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
