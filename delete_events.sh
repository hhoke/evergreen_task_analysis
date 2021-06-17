#!/bin/bash
set -xeou pipefail
# This script is intended to delete events off of a particular collection of an mongodb primary for mci.
# It is not intended to be run in parallel.
# This is intended to be more or less a single-use script to do with EVG-14707. 
# This script will fail if there is a problem in any of the executions, including remote executions, because of the bash preamble.
# sample usage: ./get_task_data.sh 

function run_script_on_db {
	db_host=$1
	js_file=$2
	scp $js_file $db_host:~/
	ssh $db_host "mongo $js_file"
	# clean up
	ssh $db_host rm $js_file
}

# make sure db_host is a primary
DB_HOST=evergreendb-1.10gen-mci.4085.mongodbdns.com
# should be as relative as possible to ease remote execution
JS_FILE=delete_task_events.js

run_aggregation "$DB_HOST" "$JS_FILE"

