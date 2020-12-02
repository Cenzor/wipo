import sys
import threading
from time import sleep
from random import randint
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as BS
import unicodedata
from handle_db import insert_db
from tools import is_proxy_alive


class WipoThread(threading.Thread):

    def __init__(self, name, domain, search_query, proxy_list, page_count):
        threading.Thread.__init__(self)
        self.name = name
        self.domain = domain
        self.search_query = search_query
        self.page_count = page_count
        self.proxy_list = proxy_list
        self.init_driver()
        print(f'{self.name}:Start with domain={self.domain},'
              f' search_query={self.search_query},'
              f' proxy={self.proxy}')
        self.statistic = dict()
        self.brand_data = []

    def run(self):
        self.main()

    def main(self):
        self.parse()
        self.driver.quit()

    # TODO: chromedriver засунуть в bin
    # Инициализация драйвера
    def init_driver(self):
        print(f'{self.name}:Init webdriver')
        while True:
            temp_proxy = self.proxy_list.get()
            print(f'{self.name}:Try proxy {temp_proxy}...')
            print(f'Length of proxies_list: {self.proxy_list.qsize()}')
            if is_proxy_alive(temp_proxy):
                self.proxy = temp_proxy
                self.proxy_list.put(temp_proxy)
                print(f'Length of proxies_list: {self.proxy_list.qsize()}')
                print(f'{self.name}:...{self.proxy} alive')
                break
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64)"
                                    " AppleWebKit/537.36 (KHTML, like Gecko)"
                                    " Chrome/87.0.4280.66 Safari/537.36")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'--proxy-server={self.proxy}')
        self.driver = webdriver.Chrome('./chromedriver',
                                       options=chrome_options)
        # driver = webdriver.Chrome('/usr/bin/chromedriver')
        print(f'{self.name}:Complete')

    def parse(self):
        attempt = 1
        while True:
            # Открыть начальную страницу
            print(f'{self.name}:Open start page, attempt {attempt}...')
            self.driver.get('https://www3.wipo.int/branddb/en/')
            locate_element = '//*[@id="results"]/div[1]/div[2]/a/span[1]/img'
            if self.wait_element_present(locate_element):
                break
            if attempt == 3:
                self.init_driver()
                attempt = 0
            attempt += 1

        try:
            # Выполнить поиск по запросу
            print(f'{self.name}:Search by query...')
            inp_text = self.driver.find_element_by_xpath('//*[@id="BRAND_input"]')
            inp_text.send_keys(self.search_query)
            inp_text.send_keys(Keys.ENTER)
            sleep(randint(4, 6))
            print(f'{self.name}:...Complete')
            # Отображать по 100 результатов на странице
            print(f'{self.name}:'
                  'Set 100 result per page...')
            self.driver.find_element_by_xpath(
                '//*[@id="results"]/div[1]/div[2]/div[2]/span/div[2]'
                '/ul/li/a/span[2]') \
                .click()
            print(f'{self.name}:'
                  '...Listbox clicked...')
            sleep(randint(2, 3))
            self.driver.find_element_by_xpath(
                '//*[@id="results"]/div[1]/div[2]/div[2]/span/div[2]'
                '/ul/li/ul/li[4]/a') \
                .click()
            print(f'{self.name}:'
                  '...Row "100" clicked...')
            sleep(randint(4, 6))
            print(f'{self.name}:...Complete')
            # преобразуем page_source в экземпляр BS
            soup = BS(self.driver.page_source, 'lxml')
            self.get_statistic(soup)
            insert_db(self.statistic, 'stat')
            self.get_brand_data(soup)
            insert_db(self.brand_data, 'brand')

        except Exception as ex:
            print('In parse: ', ex)
            self.driver.quit()

    # Ожидание загрузки страницы до появления искомого элемента
    def wait_element_present(self, element):
        try:
            print(f'{self.name}:...Wait for'
                  ' the element to apear...')
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, element))
            )
            print(f'{self.name}:'
                  '...Element found...')
            return True
        except Exception as ex:
            print(f'{self.name}:'
                  f'...Element not found: ex={ex}')
            return False
            # self.driver.quit()

    # сбор данных с вкладки Source
    def get_statistic(self, soup):
        # Сохранение значений вкладки Source в список
        for list_a in soup.select('#source_filter > div.facetContainer '
                                  '> div > div.facetCounts.columns_3 > div'):
            self.statistic['search_query'] = self.search_query
            total_raw = soup.select('#results > div.results_navigation.'
                                    'top_results_navigation.displayButtons > '
                                    'div.results_pager.ui-widget-content > '
                                    'div.pagerPos')
            total = total_raw[0].string.split('/')[1].strip().replace(',','')
            self.statistic['total'] = int(total)
            for a in list_a:
                value = int(a.div.findNext('div').contents[0].replace(',', ''))
                self.statistic[a.div.label.string] = value

    # сбор основных данных по поисковому запросу (100х10)
    # TODO: добавиьт в лог self.query
    def get_brand_data(self, soup):
        page = 1
        table = soup.find_all('table')[4]
        self.brand_data_processing(table, page)
        while page < self.page_count:
            print(f'{self.name}:Click to the next page button...')
            # Если следующей страницы нет, тогда заканчиваем сбор данных
            try:
                btn_next = self \
                    .driver \
                    .find_element_by_xpath('//*[@id="results"]/div[1]/div[2]'
                                           '/div[3]/a[1]/span[1]')
                btn_next.click()
            except Exception:
                print(f'{self.name}:...Next page doesnt exist, break')
                break
            print(f'{self.name}:...clicked.')
            sleep(randint(4, 5))
            soup = BS(self.driver.page_source, 'lxml')
            table = soup.find_all('table')[4]
            self.brand_data_processing(table, page+1)
            # break  # для первых двух страниц
            page += 1

    # извлечение данных из таблицы
    # TODO: добавить в лог номер обрабатываемой строки
    def brand_data_processing(self, table, page):
        # Brand 6, Source 7, Status 8, Relevance 9, Origin 10, Holder 11,
        # Holder Country 12, Number 13, App. Date 15, Image Class 17,
        # Nice Cl. 18, Image 19
        print(f'{self.name}:Extract data from page={page}')
        for tr in table.find_all('tr')[1:]:
            tds = tr.find_all('td')
            temp_list = [
                self.domain, self.search_query, tds[6]['title'],
                tds[7]['title'], tds[8]['title'], tds[9]['title'],
                tds[10]['title'], tds[11]['title'], tds[12]['title'],
                tds[13]['title'], tds[15]['title'], tds[17]['title'],
                tds[18]['title'], tds[19]['title']
            ]
            row_tuple = tuple(
                map(lambda x: unicodedata.normalize('NFKD', x).strip(),
                    temp_list))
            self.brand_data.append(row_tuple)
            # break  # для первой строки
