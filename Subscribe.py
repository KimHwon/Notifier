import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import redis
import time

DM_HOOK_URL = os.environ.get('DM_HOOK_URL')
REDIS_TLS_URL = os.environ.get('REDIS_TLS_URL')
REDIS_URL = os.environ.get('REDIS_URL')
SAVE_FILE = None #'subscribe_config.json'

class SubscribableObject:
    def load(self, data):
        raise NotImplementedError()
    def save(self, data):
        raise NotImplementedError()
    def fetch(self):
        raise NotImplementedError()

class HongikCE(SubscribableObject):
    def __init__(self):
        self.base_url = 'http://www.hongik.ac.kr'
        self.list_url = '/front/boardlist.do?bbsConfigFK=54'
        self.last_visit = 0

    def load(self, data):
        self.last_visit = data['last_visit']
    def save(self, data):
        data['last_visit'] = self.last_visit

    def parse_article(self, article_url):
        time.sleep(1)

        res = requests.get(urljoin(self.base_url, article_url))
        if res.status_code != 200:
            raise Exception(f'Request failed. [{self.__class__.__name__}]{res.url}: {res.status_code}')
        
        soup = BeautifulSoup(res.text, 'html.parser')
        body_text = ''
        for paragraph in soup.select_one('div.substance').find_all(recursive=False):
            body_text += f'{paragraph.text.strip()}'
            if body_text.rfind('\n\n') != 0:    # limit line break twice
                body_text += '\n'

        return body_text

    
    def fetch(self):
        messege_list = []

        res = requests.get(urljoin(self.base_url, self.list_url))
        if res.status_code != 200:
            raise Exception(f'Request failed. [{self.__class__.__name__}]{res.url}: {res.status_code}')

        soup = BeautifulSoup(res.text, 'html.parser')
        article_list = soup.select('div.bbs-list > table > tbody > tr')
        if not article_list:
            raise Exception(f'Parse html failed. [{self.__class__.__name__}]')

        for article in reversed(article_list):
            idx_str = article.find('td').text   # first <td> elem

            if idx_str.isdigit():
                idx = int(idx_str)
                if idx > self.last_visit:
                    # do something
                    article_url = article.select_one('div.subject > a')['href']

                    title = article.select_one('div.subject > a > span').text.strip()
                    body = self.parse_article(article_url)

                    messege_list.append(f'*{title}*\n{body}')

                    self.last_visit = idx
        
        return messege_list


if __name__ == '__main__':
    from_db = not SAVE_FILE
    instance_list = [HongikCE()]
    
    save_data = None
    if from_db:
        with redis.StrictRedis.from_url(REDIS_URL) as db:
            save_data = json.loads(
                db.get('subscribe_config').decode('utf-8')
                )
    else:
        with open('subscribe_config.json', 'r') as fp:
            save_data = json.load(fp)
            

    for instance in instance_list:
        instance.load(save_data[instance.__class__.__name__])
        fetch_data = instance.fetch()

        if isinstance(fetch_data, str):
            requests.post(DM_HOOK_URL, json={"text": str(fetch_data)})

        elif isinstance(fetch_data, list):
            for text in fetch_data:
                requests.post(DM_HOOK_URL, json={"text": str(text)})

        instance.save(save_data[instance.__class__.__name__])


    if from_db:
        with redis.StrictRedis.from_url(REDIS_URL) as db:
            db.set(
                'subscribe_config',
                json.dumps(save_data).encode('utf-8')
                )
    else:
        with open(SAVE_FILE, 'r') as fp:
            json.dump(save_data, fp)