rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
	{$match: {finish_time: {$gt: ISODate("2020-09-16T00:00:00.000Z")}}},
	{$match: {finish_time: {$lt: ISODate("2020-09-17T00:00:00.000Z")}}},
	{$match: {"details.status": "failed"}},
	{$match: {"details.type": "system"}},
	{$match: {"details.desc": "stranded"}},
	{$project: {"finish_time": 1, "scheduled_time": 1}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
