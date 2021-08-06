rs.secondaryOk();
db = db.getSiblingDB('mci');
function problemChild(){
return db.tasks.aggregate([
{$match: {build_id: 'mongodb_mongo_master_enterprise_windows_all_feature_flags_suggested_b46c44c41849606ade03f8a9238aa6ea800bb87a_21_08_06_18_35_46'}},
{$project: {create_time:1, dispatch_time:1, scheduled_time:1, start_time:1, finish_time:1, priority:1, distro:1, depends_on:1, version:1, display_only:1, generated_by:1, task_group:1}},
])};
//toArray makes this valid json for later loading into python
var x = problemChild().toArray();
printjson(x)
//{$match: {distro: 'rhel62-small' }},
