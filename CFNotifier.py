import json
import requests
import time
import os

DM_HOOK_URL = os.environ.get('DM_HOOK_URL')
CHANNEL_HOOK_URL = os.environ.get('CHANNEL_HOOK_URL')
THRESHOLD_HOUR = 18

try:
    res = requests.get('https://codeforces.com/api/contest.list')
    if res.status_code != 200:
        raise Exception(f'Request failed. [1] {res.status_code}')

    contest_data = json.loads(res.content)
    if not contest_data['status'] == 'OK':
        raise Exception('Request failed. [2]')

    messege_str = ''
    for contest in contest_data['result']:
        if not contest['phase'] == 'BEFORE':
            continue

        if not int(contest['relativeTimeSeconds']) > -3600*THRESHOLD_HOUR:
            continue

        time_str = time.strftime('%H:%M', time.localtime(contest['startTimeSeconds']))
        name_str = contest['name']
        url_str = f'https://codeforces.com/contests/{contest["id"]}'

        messege_str += f'[{time_str}] {name_str} : {url_str}\n'


    if len(messege_str) > 0:
        res = requests.post(CHANNEL_HOOK_URL, json={"text": messege_str})
        if res.status_code != 200:
            raise Exception(f'Request failed. [3] {res.status_code}')
    #requests.post(DM_HOOK_URL, json={"text": "Triggered!"})

except Exception as ex:
    requests.post(DM_HOOK_URL, json={"text": str(ex)})