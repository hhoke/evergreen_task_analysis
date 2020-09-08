import json


with open('./mms_system_failures.json') as f:
    j = json.load(f)

description_keywords = { 'stranded':0, 'git.get_project':0, 'host.list':0, 'subprocess.exec':0, } 

missing = 0

for t in j:
    key_found = False
    for keyword in description_keywords:
        try:
            if keyword in t['details']['desc']:
                description_keywords[keyword] +=1
                key_found = True

        except KeyError:
            missing += 1
            key_found = True
    if not key_found:
        print(t)

print('Missing detail description: {}'.format(missing))
for key in description_keywords:
    print('{}: {}'.format(description_keywords[key], key))
print('{} total'.format(len(j)))
