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


# Количество страниц для сбора
PAGE_COUNT = 10


class WipoThread(threading.Thread):

    def __init__(self, name, domain, search_query):
        threading.Thread.__init__(self)
        self.name = name
        self.domain = domain
        self.search_query = search_query
        self.driver = self.init_driver()
        self.source_tab_list = []
        self.brand_data = []
        print(f'{self.name} init with {self.domain=}, {self.search_query=}')

    def run(self):
        self.main()

    def main(self):
        self.parse()
        print(f'{self.name}:Length of brand_data: {len(self.brand_data)}')
        print(self.brand_data[0])
        self.driver.quit()

    # Инициализация драйвера
    def init_driver(self):
        print(f'{self.name}:Init webdriver')
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64)"
                                    " AppleWebKit/537.36 (KHTML, like Gecko)"
                                    " Chrome/87.0.4280.66 Safari/537.36")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome('/usr/bin/chromedriver',
                                  options=chrome_options)
        # driver = webdriver.Chrome('/usr/bin/chromedriver')
        print(f'{self.name}:Complete')
        return driver

    # Получение данных со вкладки Source
    def parse(self):
        while True:
            # Открыть начальную страницу
            print(f'{self.name}:Open start page...')
            self.driver.get('https://www3.wipo.int/branddb/en/')
            locate_element = '//*[@id="results"]/div[1]/div[2]/a/span[1]/img'
            if self.wait_element_present(locate_element):
                break
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
            self.get_source_data(soup)
            self.get_brand_data(soup)
        except Exception as ex:
            print(ex)
            self.driver.quit()
            sys.exit(0)

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
                  f'...Element not found: {ex=}')
            return False
            self.driver.quit()
            sys.exit(0)

    # сбор данных с вкладки Source
    def get_source_data(self, soup):
        # Сохранение значений вкладки Source в список
        for list_a in soup.select('#source_filter > div.facetContainer '
                                  '> div > div.facetCounts.columns_3 > div'):
            for a in list_a:
                self.source_tab_list.append(
                    [
                        self.search_query,
                        a.div.label.string,
                        a.div.findNext('div').contents[0]
                    ]
                )

    # сбор основных данных по поисковому запросу (100х10)
    # TODO: добавиьт в лог self.query
    def get_brand_data(self, soup):
        """
        index 6 = column Brand, index 7 = column Source,
        index 8 = column Status, index 9 = column Relevance,
        index 10 = column Origin, index 11 = column Holder,
        index 12 = column Holder Country, index 13 = column Number,
        index 15 = column App. Date, index 17 = column Image Class,
        index 18 = column Nice Cl.
        """
        page = 1
        table = soup.find_all('table')[4]
        self.brand_data_processing(table, page)
        while page < PAGE_COUNT:
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
        print(f'{self.name}:Extract data from {page=}')
        for tr in table.find_all('tr')[1:]:
            tds = tr.find_all('td')
            temp_list = [
                self.domain, self.search_query, tds[6]['title'],
                tds[7]['title'], tds[8]['title'], tds[9]['title'],
                tds[10]['title'], tds[11]['title'], tds[12]['title'],
                tds[13]['title'], tds[15]['title'], tds[17]['title'],
                tds[18]['title']
            ]
            row_tuple = tuple(
                map(lambda x: unicodedata.normalize('NFKD', x).strip(),
                    temp_list))
            self.brand_data.append(row_tuple)
            # break  # для первой строки
