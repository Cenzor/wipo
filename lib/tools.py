import argparse
import re
from multiprocessing import Queue
from .logger_conf import configure_logger
import requests
import threading


logger = configure_logger(__name__)


def is_proxy_available(proxy, thread_name):
    proxies = {'https': proxy}
    try:
        response = requests.get('https://www3.wipo.int/branddb/en/',
                                proxies=proxies, timeout=5)
        if response.status_code == 200:
            logger.info(f'{thread_name}:Proxy {proxy} available. '
                        f'Status code: {response.status_code}')
            return True
        else:
            logger.debug(f'{thread_name}:Proxy {proxy} BANNED. Status code: '
                         f'{response.status_code}')
            return False
    except Exception:
        logger.debug(f'{thread_name}:Proxy {proxy} unavailable')
        return False


def fill_proxy_list(proxies_file):
    proxy_list = Queue()
    with open(proxies_file, 'r') as f_in:
        for line in f_in:
            proxy_list.put(line.strip())
    logger.debug(f'Length of proxy_list: {proxy_list.qsize()}')
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
    logger.debug(f'Initial params: queries_file={queries_file}, '
                 f'threads={threads}, proxies_file={proxies_file}, '
                 f'page_count={page_count}')
    return queries_file, threads, proxies_file, page_count


def get_search_queries(queries_file):
    queries = []
    with open(queries_file, 'r') as f_in:
        for line in f_in:
            # в каждой строке находим значение domain и search_query
            domain, query = line.split(None, 1)
            domain = re.sub('[\t\n]', '', domain)
            query = re.sub('[\t\n]', '', query)
            queries.append((domain, query,))
    queries.reverse()
    logger.debug(f'Length of queries: {len(queries)}')
    return queries
