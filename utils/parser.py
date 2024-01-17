import time

import requests

from bs4 import BeautifulSoup
from utils.utils import get_current_time, get_requests, print_template

DOMAIN = 'https://www.santech.ru'


def parse_characteristics(div_elements):
    """
    Парсит характеристики, представленные в виде списка элементов <div>.
    Args:
        div_elements (list): Список элементов <div>, содержащих характеристики.
    Returns:
        dict: Словарь, содержащий характеристики, где ключи - это названия характеристик,
              а значения - их значения.
    """

    characteristics = {}

    current_key = None
    for div in div_elements:
        if not div.find('div'):
            current_key = div.get_text(strip=True).replace('"', "'")
        else:
            if current_key:
                characteristics[current_key] = div.get_text(strip=True).replace('"', "'")
                current_key = None
    return characteristics


def parse_category_links(url):
    """
    Извлекает ссылки на категории из веб-страницы каталога.
    Args:
        url (str): URL веб-страницы каталога, откуда нужно извлечь ссылки.
    Returns:
        list: Список объектов BeautifulSoup, представляющих ссылки на категории.
    """

    response = get_requests(f'{url}/catalog/')
    if not response:
        return False

    soup = BeautifulSoup(response.text, 'html.parser')
    catalog_categories = soup.find('div', 'ss-catalog-categories')
    category_links = catalog_categories.find_all('a')
    return category_links


def start_site_parsing(product):
    """
    Парсит информацию о продукте с веб-страницы и возвращает список словарей с характеристиками.

    Args:
        product (str): URL веб-страницы продукта.

    Returns:
        list: Список словарей, каждый из которых содержит характеристики продукта.
              В случае ошибки во время парсинга, возвращается пустой список.
    """
    try:
        product_lists = []

        # Отправляем GET-запрос для получения веб-страницы продукта
        response = requests.get(product)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Удаляем элементы с классом 'tip a-inline-block', если они есть
        tips = soup.find_all('div', 'tip a-inline-block')
        for tip in tips:
            tip.decompose()

        characteristics = {}

        # Извлекаем хлебные крошки
        breadcrumbs = soup.find('nav', 'ss-breadcrumbs').find('ul').find_all(attrs={'itemprop': 'title'})

        # Проверяем наличие ключевых элементов для определения типа страницы
        if soup.find('div', 'ss-product-other-variants') and soup.find('div', 'ss-product-other-variants').find('h2', 'ss-category-title').get_text(strip=True) == 'ВАРИАНТЫ ТОВАРА' and soup.find('div', 'ss-product-other-variants').find('table', 'ss-product-other-variants__table'):
            root_div = soup.find('table', 'ss-product-other-variants__table')
            tr_elements = root_div.find('tbody').find_all('tr')

            for i in range(2, len(tr_elements), 3):
                characteristics = {}

                characteristics['Категория'] = breadcrumbs[2].get_text(strip=True)
                characteristics['Раздел'] = breadcrumbs[3].get_text(strip=True)
                characteristics['Время парсинга (мск)'] = get_current_time()
                characteristics['Город'] = soup.find('div', 'ss-header-desktop__regions').find('a', 'ss-regions__selected').get_text(strip=True)
                characteristics['Телефон города'] = soup.find('div', 'ss-header-desktop__contacts-phone').find('a').get_text(strip=True)

                if tr_elements[i - 2].find('td').find('a'):
                    url = DOMAIN + tr_elements[i - 2].find('td').find('a')['href']
                    tr_elements[i - 2].find('td').find('a').decompose()
                else:
                    url = product

                div_elements = tr_elements[i].find('td').find('div', 'ss-product-property--extralight-grey').find_all('div', class_=False)
                prices_elements = tr_elements[i].find('div', 'ss-col-12 ss-col-xl-4 ss-col-md-5 ss-js-price').find_all('p', recursive=False)

                for item in prices_elements:
                    prices = item.get_text(strip=True).split(' —')
                    characteristics[prices[0]] = prices[1]

                characteristics['Наименование'] = tr_elements[i - 2].find('td').get_text(strip=True)[2:].replace('"', "'")
                characteristics['URL товара'] = url
                characteristics.update(parse_characteristics(div_elements))

                # Добавляем словарь с характеристиками в список продуктов
                product_lists.append(characteristics)
        else:
            root_div = soup.find('div', 'ss-col ss-mb-20').find('div', 'ss-product-property')
            div_elements = root_div.find_all('div', class_=None, recursive=False)

            characteristics['Категория'] = breadcrumbs[2].get_text(strip=True)
            characteristics['Раздел'] = breadcrumbs[3].get_text(strip=True)
            characteristics['Время парсинга (мск)'] = get_current_time()
            characteristics['Город'] = soup.find('div', 'ss-header-desktop__regions').find('a', 'ss-regions__selected').get_text(strip=True)
            characteristics['Телефон города'] = soup.find('div', 'ss-header-desktop__contacts-phone').find('a').get_text(strip=True)
            characteristics['Наименование'] = soup.find('h1', 'ss-category-title').get_text(strip=True).replace('"', "'")
            characteristics['URL товара'] = product
            if soup.find('div', 'ss-product-info__price').find('b'):
                characteristics['Цена'] = soup.find('div', 'ss-product-info__price').find('b').get_text(strip=True)
            else:
                characteristics['Цена'] = soup.find('div', 'ss-product-info__box').find('div', 'ss-mt-10').find('b').get_text(strip=True)

            characteristics.update(parse_characteristics(div_elements))
            product_lists.append(characteristics)
        return product_lists
    except Exception as ex:
        return []

