rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
	{$match: {finish_time: {$gt: ISODate("2020-09-14T04:00:00.000Z")}}},
	{$match: {finish_time: {$lt: ISODate("2020-09-15T04:00:00.000Z")}}},
	{$match: {distro : "suse12-small"}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
