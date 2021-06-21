// intended to use to delete events from an evergreen primary
db = db.getSiblingDB('mci');
max_items_to_delete = 500000;
beginning_of_time = ISODate("2014-01-27T21:23:26.295Z")
function deleteStuff(delete_before_datetime){
	num_items_to_delete = db.event_log.count( {r_type:"TASK", ts:{$lte:delete_before_datetime}} );
	if (num_items_to_delete < max_items_to_delete) {
		divisor = num_items_to_delete / max_items_to_delete;
		time_since_beginning = delete_before_datetime - beginning_of_time;
		deleteStuff(beginning_of_time + (time_since_beginning/divisor));
	} else {
		num_items_to_delete = db.event_log.count( {r_type:"TASK", ts:{$lte:delete_before_datetime}} );
	}	
}
deleteStuff(ISODate("2014-02-27T21:23:26.295Z")});
