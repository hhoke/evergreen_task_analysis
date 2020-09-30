rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
	{$match: {version: "mms_b501148c740bd81c273af3cb3da11ea2b4da69d9"}},
	{$project: {finish_time: 1, start_time: 1, scheduled_time: 1, create_time:1, depends_on: 1, version:1, distro:1}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
