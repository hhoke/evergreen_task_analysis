rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
	{$match: {version: "mongodb_mongo_v4.4_8795ab9b5b2269203968d2061e286e2de45b4cad"}},
	{$project: {finish_time: 1, start_time: 1, scheduled_time: 1, create_time:1, depends_on: 1, version:1, distro:1}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
