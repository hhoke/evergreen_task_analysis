rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
	{$match: {finish_time: {$gt: ISODate("2020-08-25T20:00:00.000Z")}}},
	{$match: {finish_time: {$lt: ISODate("2020-09-08T20:00:00.000Z")}}},
	{$match: {"details.status": "failed"}},
	{$match: {"details.type": "system"}},
	{$match: {version: {$regex: '^mms.*'}}},
	{$project: {"details.desc": 1}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
