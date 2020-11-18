#!/usr/bin/env python3
''' fetches recent patches from the evergreen API and passes them on for further processing
'''
import requests
import yaml
import os
import logging

# from Sam's evergreen_distro_clone.py 
def _get_api_info(cred_file):
    cred_file = os.path.expanduser(cred_file)

    if not os.path.exists(cred_file):
        logging.error("credential file does not exist")
        exit(1)

    with open(cred_file, "r") as f:
        data = yaml.safe_load(f)

        return {"Api-Key": data["api_key"], "Api-User": data["user"]}

def _get_patches(token):
    response = requests.get('https://evergreen.mongodb.com/rest/v2/projects/mms/patches?limit=3000', headers=token)
    response.raise_for_status()
    data = response.json()
    patch_ids = []
    for item in data:
        if item['status'] == 'succeeded':
            if len(item['tasks']) < 30:
                continue
            patch_ids.append(item['patch_id'])
    return patch_ids 

def get_recent_patches():
    
    token = _get_api_info('~/.evergreen.yml')
    return _get_patches(token)

successful_path_ids = get_recent_patches()

for _id in successful_path_ids:
   os.system('./foobarize.sh {} pipenv run ./DependencyAnalysis.py'.format(_id)) 
