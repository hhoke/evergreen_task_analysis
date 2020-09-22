rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.old_tasks.aggregate([
	{$match: {finish_time: {$gt: ISODate("2020-09-17T19:00:00.000Z")}}},
	{$match: {finish_time: {$lt: ISODate("2020-09-18T19:00:00.000Z")}}},
	{$match: {"details.status": "failed"}},
	{$match: {"details.type": "system"}},
	{$match: {"details.desc": "stranded"}},
	{$project: {"finish_time": 1, "start_time": 1}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
