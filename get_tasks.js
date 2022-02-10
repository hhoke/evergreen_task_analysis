rs.slaveOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.event_log.aggregate([
{$match: {
	e_type: "PROJECT_MODIFIED",
	ts: {$gt: ISODate("2022-01-24T15:30:00.000Z")},
	ts: {$lt: ISODate("2022-01-25T12:00:00.000Z")},
}}
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
