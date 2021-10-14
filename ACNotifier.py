from bs4 import BeautifulSoup
import requests
from dateutil.parser import parse
from datetime import datetime
import os

DM_HOOK_URL = os.environ.get('DM_HOOK_URL')
CHANNEL_HOOK_URL = os.environ.get('CHANNEL_HOOK_URL')
THRESHOLD_HOUR = 24

try:
    res = requests.get('https://atcoder.jp/contests/')
    if res.status_code != 200:
        raise Exception(f'Request failed. [1] {res.status_code}')

    messege_str = ''

    soup = BeautifulSoup(res.text, 'html.parser')
    tr_list = soup.select('#contest-table-upcoming > div > div > table > tbody > tr')
    for tr in tr_list:
        timestamp = tr.select_one('time').get_text(strip=True)
        title = tr.select_one('td:nth-child(2)')

        start_time = parse(timestamp)
        if (start_time - datetime.now().astimezone()).total_seconds() < 3600*THRESHOLD_HOUR:
            time_str = start_time.strftime('%H:%M')
            name_str = title.get_text(strip=True)[1:]
            url_str = f"https://atcoder.jp{title.select_one('a')['href']}"

            messege_str += f'[{time_str}] {name_str} : {url_str}\n'


    if len(messege_str) > 0:
        res = requests.post(CHANNEL_HOOK_URL, json={"text": messege_str})
        if res.status_code != 200:
            raise Exception(f'Request failed. [3] {res.status_code}')
    #requests.post(DM_HOOK_URL, json={"text": "Triggered!"})

except Exception as ex:
    requests.post(DM_HOOK_URL, json={"text": str(ex)})