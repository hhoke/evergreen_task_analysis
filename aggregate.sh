#!/bin/bash
set -xeou pipefail
# This scipt is intended to download data from one of the mongodb secondary databases to the local machine
# it is not intended to be run in parallel
# sample usage: ./aggregate.sh && TaskWaitsByFinishTime.py

function run_aggregation {
	db_host=$1
	js_file=$2
	scp_file=$3
	scp $js_file $dp_host:~/
	ssh $dp_host mongo $js_file > $scp_file
	scp $dp_host:~/$scp_file ./
	# clean up
	ssh $dp_host rm $js_file $scp_file
}

function clean_results {
	in_file=$1
	# convert the JSON into something more easily read by python
	sed 's/ISODate(//g' $in_file > munged.json
	sed 's/)//g' munged.json > munged2.json
	sed 's/NumberLong(//g' munged2.json > munged_$in_file
	# clean up
	rm munged.json munged2.json
}

# make sure db_host is not a primary!
DB_HOST=evergreendb-1.10gen-mci.4085.mongodbdns.com
# should be as relative as possible to ease remote execution
JS_FILE=get_tasks.js

SCP_FILE='/tmp/result.json'
OUT_FILE=rhel62_08-05-2020.json

run_aggregation "$DB_HOST" "$JS_FILE" "$SCP_FILE"
clean_results "$SCP_FILE" "$OUT_FILE"

