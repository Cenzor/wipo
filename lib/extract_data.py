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
from .handle_db import insert_db
from .tools import is_proxy_available
from .logger_conf import configure_logger
import traceback
import sys


logger = configure_logger(__name__)


class WipoThread(threading.Thread):

    def __init__(self, name, domain, search_query, proxy_list, page_count):
        threading.Thread.__init__(self)
        self.name = name
        self.logger = logger
        self.domain = domain
        self.search_query = search_query
        self.page_count = page_count
        self.proxy_list = proxy_list
        self.init_driver()
        self.logger.info(f'{self.name}:Started with domain={self.domain},'
                         f' search_query={self.search_query},'
                         f' proxy={self.proxy}')
        self.statistic = dict()
        self.brand_data = []

    def run(self):
        self.main()

    def main(self):
        self.parse()
        self.logger.info(f'{self.name}:Finished work')
        self.driver.quit()

    def init_driver(self):
        self.logger.debug(f'{self.name}:Init webdriver')
        # Выбор и проверка прокси из очереди. 
        while True:
            temp_proxy = self.proxy_list.get()
            self.logger.debug(f'{self.name}:Try proxy {temp_proxy}...')
            if is_proxy_available(temp_proxy, self.name):
                self.proxy = temp_proxy
                self.proxy_list.put(temp_proxy)
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
        self.driver = webdriver.Chrome('/usr/bin/chromedriver',
                                       options=chrome_options)

    def parse(self):
        attempt = 1
        # Открытие начальной страницы и обнаружение элемента,
        # для подтверждения полной загрузки страницы.
        # По истечению трёх попыток берётся другой прокси.
        while True:
            self.logger.debug(f'{self.name}:Open start page, '
                              f'attempt {attempt}...')
            self.driver.get('https://www3.wipo.int/branddb/en/')
            # Для проверки полной загрузки выбрано изображение "TM view"
            # в заголовке таблицы с выдачей результатов
            locate_element = '//*[@id="results"]/div[1]/div[2]/a/span[1]/img'
            if self.wait_element_present(locate_element):
                break
            if attempt == 3:
                self.init_driver()
                attempt = 0
            attempt += 1

        try:
            # Выполнить поиск по запросу в поле "Text"
            self.logger.debug(f'{self.name}:Search by query...')
            inp_text = self.driver.find_element_by_xpath(
                '//*[@id="BRAND_input"]'
            )
            inp_text.send_keys(self.search_query)
            inp_text.send_keys(Keys.ENTER)
            sleep(randint(4, 6))
            self.logger.debug(f'{self.name}:...Complete')
            # Отображать по 100 результатов на странице
            self.logger.debug(f'{self.name}:Set 100 result per page...')
            # TODO: тестирование неправиьлного элемента ABC
            # Раскрывающийся список в заголовке таблицы с выдачей результатов
            self.driver.find_element_by_xpath(
                '//*[@id="results"]/div[1]/div[2]/div[2]/span/div[2]'
                '/ul/li/a/span[2]') \
                .click()
            self.logger.debug(f'{self.name}:...Listbox clicked...')
            sleep(randint(2, 3))
            self.driver.find_element_by_xpath(
                '//*[@id="results"]/div[1]/div[2]/div[2]/span/div[2]'
                '/ul/li/ul/li[4]/a') \
                .click()
            self.logger.debug(f'{self.name}:...Row "100" clicked...')
            sleep(randint(4, 6))
            self.logger.debug(f'{self.name}:...Complete')
            # преобразуем исходный код страницы, полученный от webdriver,
            # в объект BeautifulSoup для разбора
            soup = BS(self.driver.page_source, 'lxml')
            self.logger.debug(f'{self.name}Get statistics data')
            self.get_statistic(soup)
            self.logger.debug(f'{self.name}Insert statistic data to db')
            insert_db(self.statistic, 'stat', self.name)
            self.logger.debug(f'{self.name}Get brand data')
            self.get_brand_data(soup)
            self.logger.debug(f'{self.name}Insert brand data to db')
            insert_db(self.brand_data, 'brand', self.name)
        except Exception as ex:
            self.logger.debug(f'{self.name}:Error occurred - {ex}')
            self.logger.debug(f'{self.name}:'
                              f'{traceback.print_exception(*sys.exc_info())}')
            self.driver.quit()

    # Ожидание загрузки страницы до появления искомого элемента
    def wait_element_present(self, element):
        try:
            self.logger.debug(f'{self.name}:...Wait for'
                              ' the element to apear...')
            # Таймер ожидания загрузки искомого элемента 20 сек
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, element))
            )
            self.logger.debug(f'{self.name}:'
                              '...Element found...')
            return True
        except Exception as ex:
            self.logger.debug(f'{self.name}:'
                              f'...Element not found: {ex}')
            return False

    # сбор данных с вкладки Source
    def get_statistic(self, soup):
        # Сохранение значений вкладки Source в список
        for list_a in soup.select('#source_filter > div.facetContainer '
                                  '> div > div.facetCounts.columns_3 > div'):
            self.logger.debug(f'{self.name}:Statistic table found')
            self.statistic['search_query'] = self.search_query
            # значение total в заголовке таблицы с выдачей результатов
            total_raw = soup.select('#results > div.results_navigation.'
                                    'top_results_navigation.displayButtons > '
                                    'div.results_pager.ui-widget-content > '
                                    'div.pagerPos')
            total = total_raw[0].string.split('/')[1].strip().replace(',','')
            self.statistic['total'] = int(total)
            # Добавление значений TM в словарь
            for a in list_a:
                value = int(a.div.findNext('div').contents[0].replace(',', ''))
                self.statistic[a.div.label.string] = value
            self.logger.debug(f'{self.name}:Statistics collected')

    # сбор основных данных по поисковому запросу (100х10)
    def get_brand_data(self, soup):
        page = 1
        self.logger.debug(f'{self.name}:Get table with brand data '
                          f'(search_query={self.search_query})')
        table = soup.find_all('table')[4]
        self.logger.debug(f'{self.name}:Table with brand data found')
        # Извлечение данных с первой страницы выполняется всегда
        self.brand_data_processing(table, page)
        while page < self.page_count:
            self.logger.debug(f'{self.name}:Click to the next page button...')
            # Если следующей страницы нет, тогда заканчиваем сбор данных
            try:
                btn_next = self \
                    .driver \
                    .find_element_by_xpath('//*[@id="results"]/div[1]/div[2]'
                                           '/div[3]/a[1]/span[1]')
                btn_next.click()
            except Exception:
                self.logger.debug(f'{self.name}:...Next page doesnt '
                                  'exist, break')
                break
            self.logger.debug(f'{self.name}:...clicked.')
            page += 1
            sleep(randint(4, 5))
            self.logger.debug(f'{self.name}:Convert page_source to '
                              f'BeautifulSoup page {page}')
            soup = BS(self.driver.page_source, 'lxml')
            table = soup.find_all('table')[4]
            self.brand_data_processing(table, page)

    # TODO: протестировать номер строки в логе при ошибке
    # извлечение данных из таблицы
    def brand_data_processing(self, table, page):
        # Brand 6, Source 7, Status 8, Relevance 9, Origin 10, Holder 11,
        # Holder Country 12, Number 13, App. Date 15, Image Class 17,
        # Nice Cl. 18, Image 19
        self.logger.debug(f'{self.name}:Extract data from page={page}')
        # Обработка найденной таблицы с результатами запроса,
        # добавение в список
        for row, tr in enumerate(table.find_all('tr')[1:]):
            try:
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
            except Exception as ex:
                self.logger.debug(f'{self.name}:Error occurred - {ex}')
                self.logger.debug(f'{self.name}:Page {page}, row {row}')
                trace = traceback.print_exception(*sys.exc_info())
                self.logger.debug(f'{self.name}:{trace}')
                self.driver.quit()
        self.logger.debug(f'{self.name}:Data from page={page} '
                          'extracted')

    def __str__(self):
        return self.name
