rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
	{$match: {version: "mongodb_mongo_master_f4dd1b0c7ee46c6882ffe36f08c97099fda27fbc"}},
	{$project: {finish_time: 1, start_time: 1, scheduled_time: 1, create_time:1, depends_on: 1, version:1, distro:1}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
