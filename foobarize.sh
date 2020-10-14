#!/bin/bash
set -xeou pipefail

function replace_keyword {
	keyword=$1
	replacement=$2
	perl -p -i -e "s/${keyword}/${replacement}/g" `grep -sl --exclude foobarize.sh ${keyword} * `
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
