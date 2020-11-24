from time import sleep
from datetime import datetime
from extract_data import WipoThread
from handle_db import insert_db


# global source_tab_data
source_tab = []


if __name__ == '__main__':
    st_time = datetime.now()
    # queries = ['game', 'tea', 'cat', 'dog']
    queries = [('game.com', 'game'), ('tea.com', 'tea'), ('cat.com', 'cat')]
    N = 4
    thread_list = list()
    while queries:
        for i in range(N):
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
        # Объединение собранной потоками информации
        for thread in thread_list:
            source_tab += thread.source_tab_list
        # Запись данных в БД
        insert_db(source_tab)
        # Удаление данных отработанных потоков
        source_tab.clear()
        # Очистка списка потоков
        thread_list.clear()
    print(f'Elapsed time: {datetime.now() - st_time}')
