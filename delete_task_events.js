// intended to use to delete events from an evergreen primary
db = db.getSiblingDB('mci');
function deleteStuff(){
	var bulk = db.event_log.initializeUnorderedBulkOp();
	bulk.find( {r_type:"TASK", ts:{$lte:ISODate("2014-02-27T21:23:26.295Z")}} ).remove();
	bulk.execute();
}
deleteStuff();
