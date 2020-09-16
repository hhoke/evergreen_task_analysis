rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
	{$match: {build_id : "mongodb_mongo_v4.2_enterprise_suse12_64_220d72da13180652f4986bc65a0dd95966973dd0_20_09_14_17_52_50"}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
