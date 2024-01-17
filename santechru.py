import os
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

from utils.exporter import convert_to_json, remove_old_data, save_to_sqlite
from utils.parser import parse_category_links, start_site_parsing
from utils.utils import check_reports_folder_exist, get_requests, print_template, random_sleep


os.environ['PROJECT_ROOT'] = os.path.dirname(os.path.abspath(__file__))


def start(city):
    try:
        temp = []
        DOMAIN = 'https://www.santech.ru'

        reports_folder = check_reports_folder_exist()

        if not reports_folder:
            return False

        by_city = DOMAIN if city == 'moscow' else f'{DOMAIN}/{city}'
        print(print_template(f"({city}) Parse links to categories from the main catalog..."))

        category_links = parse_category_links(by_city)
        if not category_links:
            print(print_template(f"({city}) Error parsing the main link directory!"))
            return False

        print(print_template(f"({city}) Done! Found {len(category_links)} links to product categories."))

        print(print_template(f"({city}) Parse links to subcategories from the categories catalog..."))

        subcategory_links = []
        for category_link in category_links:
            if category_link.text.strip() != "Распродажа":
                subcategory_links.append(DOMAIN + category_link['href'])

        if not subcategory_links:
            print(print_template(f"({city}) Error parsing the subcategory link directory!"))
            return False

        for subcategory_link in subcategory_links:
            response = get_requests(subcategory_link)
            if not response:
                print(print_template(f"({city}) Error parsing the subcategory link ({subcategory_link})"))
                random_sleep(1)
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            subcategories = soup.find('div', 'ss-catalog-categories--show-all')
            if not subcategories:
                print(print_template(f"({city}) Error getting the subcategories ({subcategory_link})"))
                continue

            subsubcategory_links = [DOMAIN + url['href'] for url in subcategories.find_all('a')]

            for subsubcategory_link in subsubcategory_links:
                response = get_requests(subsubcategory_link)
                if not response:
                    print(print_template(f"({city}) Error parsing the subsubcategory link ({subcategory_link})"))
                    random_sleep(1)
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                pagination = soup.find('div', 'ss-pagination__nav ss-w-100p ss-w-md-auto ss-justify-content-center ss-justify-content-md-start')

                if pagination:
                    pagination_pages = pagination.find_all('a', 'ss-pagination__page')
                    pages_index = [index.get_text(strip=True) for index in pagination_pages]
                    catalog_product = soup.find('div', 'catalog-block').find_all('div', 'ss-catalog-product__title')

                    for page in pages_index:
                        response = get_requests(subsubcategory_link + "?page=" + page)
                        if not response:
                            print(print_template(f"({city}) Error parsing page №{page}/{len(pages_index)+1}, link ({subcategory_link})"))
                            random_sleep(1)
                            continue

                        print(print_template(f"({city}) Parsing page №{page}/{len(pages_index)+1}, link ({subcategory_link})"))
                        soup = BeautifulSoup(response.text, 'html.parser')
                        catalog_product += soup.find('div', 'catalog-block').find_all('div', 'ss-catalog-product__title')
                else:
                    catalog_product = soup.find('div', 'catalog-block').find_all('div', 'ss-catalog-product__title')

                product_urls = [DOMAIN + url.findNext()['href'] for url in catalog_product]
                with ThreadPoolExecutor(max_workers=35) as executor:
                    results = executor.map(start_site_parsing, product_urls)

                products_to_save = []
                for result in results:
                    for item in result:
                        if item['URL товара'] in temp:
                            continue
                        else:
                            products_to_save.append(item)
                print(print_template(f"({city}) Save products to sqlite: {len(products_to_save)} ({subsubcategory_link})"))
                save_to_sqlite(f'{city}-', products_to_save, reports_folder)
    except:
        return False


if __name__ == '__main__':
    cities = ['ulyanovsk', 'novorossiysk', 'tumen', 'belgorod', 'spb', 'krasnodar', 'ekb', 'nn', 'magnitogorsk', 'nizhniytagil', 'novosibirsk', 'surgut', 'chelyabinsk', 'moscow']
    reports_folder = check_reports_folder_exist()

    remove_old_data(reports_folder, cities)

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(start, cities)

    total_count = convert_to_json(reports_folder, cities)
    print(f"Total count: {total_count}")
