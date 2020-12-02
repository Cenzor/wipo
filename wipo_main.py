from time import sleep
from datetime import datetime
from extract_data import WipoThread
from tools import fill_proxy_list, get_args, get_search_queries


if __name__ == '__main__':
    st_time = datetime.now()
    queries_file, threads, proxies_file, page_count = get_args()
    proxy_list = fill_proxy_list(proxies_file)
    queries = get_search_queries(queries_file)
    thread_list = list()
    while queries:
        for i in range(threads):
            if len(queries) == 0:
                break
            thread = WipoThread(
                f'wipothread {i}',
                *queries.pop(),
                proxy_list,
                page_count
            )
            print(f'Length of queries: {len(queries)}')
            thread.start()
            sleep(1)
            thread_list.append(thread)
        # Ожидание завершения потоков
        for thread in thread_list:
            thread.join()
        # Очистка списка потоков
        thread_list.clear()
    print(f'Elapsed time: {datetime.now() - st_time}')
