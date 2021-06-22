// intended to use to delete events from an evergreen primary
db = db.getSiblingDB('mci');
max_items_to_delete = 7568;
ttl_time = ISODate("2021-03-24T21:23:26.295Z")
logs_to_delete = db.event_log.find( {r_type:"TASK", ts:{$lte:ttl_time}} ).limit(max_items_to_delete).toArray();
while (logs_to_delete.length > 0) {
	sleep(1000);
	logs_ids_to_delete = logs_to_delete.map(log => log._id);
	db.event_log.deleteMany({_id: {$in:logs_ids_to_delete}});
	logs_to_delete = db.event_log.find( {r_type:"TASK", ts:{$lte:ttl_time}} ).limit(max_items_to_delete).toArray();
	printjson(logs_to_delete[0]);
}
