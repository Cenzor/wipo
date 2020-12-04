from time import sleep
from datetime import datetime
from lib.extract_data import WipoThread
from lib.tools import fill_proxy_list, get_args, get_search_queries
from lib.logger_conf import configure_logger


logger = configure_logger(__name__)


if __name__ == '__main__':
    logger.info(f'The parser is running. Start time: {datetime.now()}')
    st_time = datetime.now()
    logger.debug('Get args from cli')
    queries_file, threads, proxies_file, page_count = get_args()
    logger.debug('Fill proxy list')
    proxy_list = fill_proxy_list(proxies_file)
    logger.debug('Get search_queries')
    queries = get_search_queries(queries_file)
    thread_list = list()
    logger.info(f'Threads count: {threads}')
    logger.info(f'Page count for each search_query: {page_count}')
    logger.info(f'Initial length of queries: {len(queries)}')
    logger.info(f'Initial length of proxy_list: {proxy_list.qsize()}')
    # Организация и запуск потоков
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
            thread.start()
            sleep(1)
            thread_list.append(thread)
        # Ожидание завершения потоков
        for thread in thread_list:
            thread.join()
        # Очистка списка потоков
        thread_list.clear()
        logger.info(f'Length of queries: {len(queries)}')
        logger.info(f'Length of proxy_list: {proxy_list.qsize()}')
        logger.info(f'Loop elapsed time ({threads} threads, '
                    f'{page_count} page_count): {datetime.now() - st_time}')
    logger.info(f'Total elapsed time: {datetime.now() - st_time}')
