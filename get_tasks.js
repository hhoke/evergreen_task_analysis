rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
	{$match: {finish_time: {$gt: ISODate("2020-09-21T00:00:00.000Z")}}},
	{$match: {finish_time: {$lt: ISODate("2020-09-22T00:00:00.000Z")}}},
	{$match: {distro: "rhel62-small"}},
	{$project: {finish_time: 1, start_time: 1, scheduled_time: 1, create_time:1, depends_on: 1}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
