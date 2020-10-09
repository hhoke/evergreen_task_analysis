rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
{$match: {version: "mongodb_mongo_master_fbafa599da8f316e508d0a152586a77e85805c29"}},
{$project: {create_time:1, dispatch_time:1, scheduled_time:1, start_time:1, finish_time:1, priority:1, distro:1, depends_on:1, version:1, display_only:1}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
