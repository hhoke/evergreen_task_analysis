rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
	{$match: {finish_time: {$gt: ISODate("2020-08-27T20:00:00.000Z")}}},
	{$match: {"details.status": "failed"}},
	{$match: {version: {$regex: '^mms.*'}}},
	{$match: {"details.desc": {$not: /.*shell.exec.*/}}},
        {$match: {"details.desc": {$not: /.*subprocess.exec.*/}}},
	{$project: {"details.desc": 1}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
