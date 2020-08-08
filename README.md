This is a collection of scripts used to analyze task performance from evergreen's database.

## Current workflow:

Open `get_task_data.sh` and modify necessary variables. 
Make sure you sign into VPN, and you download off a secondary repo. 
Also make sure the output file in this script matches the input file to the python script.
Execute: `./get_task_data.sh`. This should download the data you need in json.

Then, execute `./TaskWaitsByFinishTime.py`, also with no arguments. This should open the plotly chart in a new browser window, and save it to the filesystem.
