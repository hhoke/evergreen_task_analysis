rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
	{$match: {finish_time: {$gt: ISODate("2020-09-13T00:00:00.000Z")}}},
	{$match: {depends_on: {$exists: true, $ne: []}}},
	{$match: {display_only: {$ne: true}}},
	{$project: {depends_on: 1, start_time: 1, finish_time: 1, execution: 1}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
