This is a collection of scripts used to analyze task performance data from evergreen's database.

## Current workflow:

Open `get_task_data.sh` and modify necessary variables. 
Make sure you sign into VPN, and you download off a secondary repo. 
Also make sure the output file in this script matches the input file to the python script.
Execute: `./get_task_data.sh`. (requires ssh access to db server). This should download the data you need in json.

## Setup

### graphs

`brew install cairo` in addition to pipenv install from pipfile
