rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
	{$match: {"version": "5d9b46ed2fbabe301b7435f7"}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
