import json
import logging
import math
import re
from typing import Tuple
import requests
import uuid
import os

import dukpy
from envparse import env

import scrapy
from scrapy.exceptions import CloseSpider
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor

import pandas as pd


import logging
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

class BaseSpider(scrapy.Spider):
    def closed(self, reason):
        callback_url = getattr(self, 'callback_url', None)
        callback_params_raw = getattr(self, 'callback_params', None)
        callback_params = {
            'job_id': env('SCRAPY_JOB', default=0)
        }

        if callback_params_raw is not None:
            for element in callback_params_raw.split('&'):
                k_v = element.split('=')
                callback_params[str(k_v[0])] = k_v[1]

        if callback_url is not None:
            logging.info(f"Noticed callback_url in params, sending POST request to {callback_url}")
            requests.post(callback_url, data=callback_params)

class WildberriesCommentsSpider(BaseSpider):
    name = "wb_comments"

    def __init__(self, good_url, *args, **kwargs):
        super(WildberriesCommentsSpider, self).__init__(*args, **kwargs)
        self.good_url = good_url

        self.photo = None
        self.product_name = None

    def start_requests(self):
        yield scrapy.Request(self.good_url, self.parse_good)

    def parse_good(self, response):
        imt_id, feedbacks_count = self.load_product_info(response)

        step = 1000
        skip = 0

        for _ in range(math.ceil(feedbacks_count / step)):
            request_body = {
                "imtId": imt_id,
                "skip": skip,
                "take": step,
                "order": "dateAsc"
            }

            yield scrapy.Request("https://public-feedbacks.wildberries.ru/api/v1/feedbacks/site", self.parse_comments_request, method="POST", body=json.dumps(request_body))

            skip += step

        yield {'name':self.product_name, 'photo':self.photo}

    def load_product_info(self, response):
        imt_id = None
        feedbacks_count = 0

        products_data_js = response.xpath('//script[contains(., "wb.spa.init")]/text()').get()
        
        products_data_js = re.sub('\n', '', products_data_js)
        products_data_js = re.sub(r'\s{2,}', '', products_data_js)

        products_data_js = re.sub('routes: routes,', '', products_data_js)
        products_data_js = re.sub('routesDictionary: routesDictionary,', '', products_data_js)

        products_init = re.findall(r'wb\.spa\.init\(({.*?})\);', products_data_js)[0]


        if products_init is not None and str(products_init) != '':
            interpreter = dukpy.JSInterpreter()
            evaled_data = interpreter.evaljs(f'init={products_init};init.router;')
            evaled_data2 = interpreter.evaljs(f'init={products_init};init.seoHelper;')


            if 'ssrModel' in evaled_data.keys():
                imt_id = evaled_data['ssrModel']['product']['imtId']
                feedbacks_count = evaled_data['ssrModel']['product']['feedbacks']
                self.product_name = evaled_data['ssrModel']['product']['goodsName']

            if 'items' in evaled_data2.keys():
                self.photo = evaled_data2['items'][4]['attributesDictionary']['content']


        return imt_id, feedbacks_count

    def parse_comments_request(self, response):
        feedbacks = json.loads(response.text)

        if feedbacks['feedbacks'] is None:
            raise CloseSpider('End of feedbacks reached')

        for feedback in feedbacks['feedbacks']:
            yield {
                'text': feedback['text'],
                'rating': feedback['productValuation'],
                'created_at': feedback['createdDate'],
            }


from multiprocessing import Process

def f(runner: CrawlerRunner, link:str) -> None:
    """
        Функция, отвечающая за парсинг одного товара
        @runner:CrawlerRunner - объект раннера
        @link:str - ссылка на товар Wildberries
    """
    
    deferred = runner.crawl(WildberriesCommentsSpider, good_url=link)
    deferred.addBoth(lambda _: reactor.stop())
    reactor.run(installSignalHandlers=False)
    
    return None

def parse_product(link:str, save_filename:str='data_') -> Tuple[str, str, pd.DataFrame]:
    '''
        Функция, отвечающая за создание нового парс процесса и добавление его в очередь
        @link:str - ссылка на товар wb
        @filename:str - название файла, в который будут сохраняться данные scrapy (его передавать не надо)
    '''
    filename = save_filename + str(uuid.uuid4()) + '.json'

    runner = CrawlerRunner(settings={
        "FEEDS": {
            f"{filename}": {"format": "json"},
            
        },
    })

    p = Process(target=f, args=(runner, link))
    p.start()
    p.join()

    try:
        with open(f'./{filename}') as data_json:
            data = json.loads(data_json.read())
            name, photo = data[0]['name'], data[0]['photo']     
            data = data[1:]
            data_json.close()

        data = pd.DataFrame(data)
        data.set_axis(['review', 'rate', 'created_at'], axis='columns', inplace=True)
        data['review'] = data['review'].apply(lambda x: x.strip().replace('\n',''))

        os.remove(filename)
        return name, photo, data
    except Exception as e:
        os.remove(filename)
        logging.error(f'Никита еблоид, парсер не спарсил. Ошибка: {e}')   
        raise Exception(f'Никита еблоид, парсер не спарсил. Ошибка: {e}')