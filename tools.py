import requests
import argparse
import re
from multiprocessing import Queue
from requests.exceptions import ProxyError
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def wait_element_present(driver, element):
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, element))
        )
        return True
    except Exception:
        return False


# TODO: реализовать исключение из очереди забаненных прокси
def is_proxy_alive(proxy):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64)"
                                " AppleWebKit/537.36 (KHTML, like Gecko)"
                                " Chrome/87.0.4280.66 Safari/537.36")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(f'--proxy-server={proxy}')
    driver = webdriver.Chrome('./chromedriver',
                              options=chrome_options)
    driver.get('https://www3.wipo.int/branddb/en/')
    locate_element = '//*[@id="results"]/div[1]/div[2]/a/span[1]/img'
    if wait_element_present(driver, locate_element):
        driver.quit()
        return True
    else:
        driver.quit()
        return False

    # proxies = {'https': proxy}
    # try:
    #     response = requests.get('https://www.expressvpn.com/what-is-my-ip',
    #                             proxies=proxies)
    #     if proxy.split(':')[0] in response.text:
    #         return True
    #     else:
    #         return False
    # except ProxyError:
    #     return False


def fill_proxy_list(proxies_file):
    proxy_list = Queue()
    with open(proxies_file, 'r') as f_in:
        for line in f_in:
            proxy_list.put(line.strip())
    return proxy_list


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", dest="queries_file", action="store",
                        type=str, help="File name with queries. Default file"
                        " name 'list'", default="list")
    parser.add_argument("-t", "--threads", dest="threads", action="store",
                        type=int, help="Number of threads. Default value"
                        " threads=1",
                        default=1)
    parser.add_argument("-p", "--proxy", dest="proxies_file", action="store",
                        type=str, help="File name with proxies. Default file"
                        " name 'proxies'",
                        default="proxies")
    parser.add_argument("-c", "--count", dest="page_count", action="store",
                        type=int, help="Count of pages parsed. Default value"
                        " count=1",
                        default=1)
    args = parser.parse_args()
    queries_file = args.queries_file
    threads = args.threads
    proxies_file = args.proxies_file
    page_count = args.page_count
    return queries_file, threads, proxies_file, page_count


def get_search_queries(queries_file):
    queries = []
    with open(queries_file, 'r') as f_in:
        for line in f_in:
            domain, query = line.split(None, 1)
            domain = re.sub('[\t\n]', '', domain)
            query = re.sub('[\t\n]', '', query)
            queries.append((domain, query,))
    queries.reverse()
    return queries
