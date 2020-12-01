from time import sleep
from datetime import datetime
from extract_data import WipoThread
import re
import argparse
import sys


def get_search_queries(queries_file):
    queries = []
    with open(queries_file, 'r') as f_in:
        for line in f_in:
            domain, query = line.split(None, 1)
            domain = re.sub('[\t\n]', '', domain)
            query = re.sub('[\t\n]', '', query)
            queries.append((domain, query,))
    return queries


def get_conf():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", dest="queries_file", action="store",
                        type=str, help="File name with queries. Default file"
                        " name 'list'", default="list")
    parser.add_argument("-t", "--threads", dest="threads", action="store",
                        type=int, help="Number of threads. Default value"
                        " threads=2",
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


if __name__ == '__main__':
    queries_file, threads, proxies_file, page_count = get_conf()
    # sys.exit(0)
    queries = get_search_queries(queries_file)
    queries.reverse()
    st_time = datetime.now()
    thread_list = list()
    while queries:
        for i in range(threads):
            if len(queries) == 0:
                break
            thread = WipoThread(
                f'wipothread {i}',
                *queries.pop()
            )
            thread.start()
            sleep(1)
            thread_list.append(thread)
        # Ожидание завершения потоков
        for thread in thread_list:
            thread.join()
        # Очистка списка потоков
        thread_list.clear()
    print(f'Elapsed time: {datetime.now() - st_time}')
