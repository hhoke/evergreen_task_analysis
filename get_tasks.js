rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
	{$match: {version: "mms_b2fea32bc34cc0186e3fdd29812aaf6a5b7f7a3a"}},
	{$project: {finish_time: 1, start_time: 1, scheduled_time: 1, create_time:1, depends_on: 1, version:1, distro:1}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
