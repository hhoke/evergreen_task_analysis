This is a collection of scripts used to analyze task performance data from evergreen's database.

## Usage
### typical workflow:

- Make sure you sign into VPN, and check out a new branch at the start of your investigation, ideally named after an EVG ticket. 
- Modify `get_tasks.js` to contain the desired query. If you wish, you may include the word "foobar" in a field such as the distro field to make it easier to rapidly generate figures or calculate and display metrics.
- Modify the main function of either `metrics.py` or `plots.py` to produce the plot or metric you desire. 
- run the scripts, for example:

```zsh
for distro in rhel62-large windows-64-vs2019-large rhel67-zseries-large 
for> ./foobarize.sh "$x" pipenv run ./plots.py
```
- make an archive for data and figures (if desired) with `mkdir archive_by_hash/$(git rev-parse --short HEAD)` and move json and html there.
- if you made any edits to the core functionality, merge back into master

Also make sure the output file in this script matches the input file to the python script.
Execute: `./get_task_data.sh`. (requires ssh access to db server). This should download the data you need in json.


## Setup

Repo contains a pipfile. I use [pipenv](https://pipenv-fork.readthedocs.io/en/latest/) to manage installation and dependency management.

### graphs

`brew install cairo` is needed for advanced graph functionality, in addition to the pipenv setup.

## Docs

An in-depth and continually-expanding writeup of findings and approaches can be found here:
[https://hhoke.github.io/evergreen_task_analysis/InvestigatingEvergreenPerformance.html](https://hhoke.github.io/evergreen_task_analysis/InvestigatingEvergreenPerformance.html)

