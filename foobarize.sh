#!/bin/bash
set -xeou pipefail

function replace_keyword {
	keyword=$1
	replacement=$2
	# dry run, fail if we find nothing
	grep -sl --exclude foobarize.sh --exclude patches.py ${keyword} *
	perl -p -i -e "s/${keyword}/${replacement}/g" grep -sl --exclude foobarize.sh --exclude patches.py ${keyword} *
}

function defoobarize {
	replace_keyword "foobar" "${1}"
}

function refoobarize {
	replace_keyword "${1}" "foobar"
}

# get replacement, and then remove from arg list
k=$1
shift
defoobarize $k
./get_task_data.sh
$@
refoobarize $k
