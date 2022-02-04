import requests
from bs4 import BeautifulSoup
import pandas
import lxml

import typing as tp

def get_html(url:str, params:dict=None) -> requests.models.Response:
    """
        Функция, возвращающая объект типа Response с ответом на запрос 
        @url:str - ссылка на категорию wb
        @params:dict - параметры запросаы
    """

    headers = {
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0",
    }
    html = requests.get(url, headers=headers, params=params)
    return html

def get_content(html:requests.models.Response) -> list:
    """
        Функция поиска на странице карточек с товаром
        @html:requests.models.Response - ответ сервера, из которого будем доставать html
    """
    
    soup = BeautifulSoup(html.text, 'html.parser')
    items = soup.find_all('div', class_="product-card")
    
    title = soup.h1.text
    cards = []

    for item in items:
        cards.append(f'https://www.wildberries.ru{item.find("a", class_="product-card__main").get("href")}')
        
    return cards, title

def parse_product_category(url:str) -> tp.Union[tp.Tuple[list, str], None]:
    """
        Главная функция, реализующая прасинг категории wb
        @url:str - ссылка на категорию wb
    """
    
    html = get_html(url)
    if html.status_code == 200:
        html = get_html(url, params={'sort': 'popular', 'page': 1})
        cards, title = get_content(html)
        return cards, title
    else:
        print(f'Ответ сервера:{html.status_code}. Парсинг невозможен!')
        raise Exception('Не удалось подключиться к wb через bs4')
