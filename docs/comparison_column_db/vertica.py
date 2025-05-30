import time
import uuid
from datetime import datetime
from multiprocessing import Process
from random import randint

import vertica_python
from faker import Faker
from tqdm import tqdm

DB_TABLE = "test"
NUMBER_PROCESSES = 5
NUMBER_RECORDS_PROCESS = 1_000_000
BATCH_VERTICA = 1000
QUERY = """
    INSERT INTO test (id, film_uuid, user_uuid, message, value, timestamp)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
connection_info = {
    "host": "127.0.0.1",
    "port": 5433,
    "user": "dbadmin",
    "password": "",
    "database": "docker",
    "autocommit": True,
}


def create_table():
    with vertica_python.connect(**connection_info) as conn:
        client = conn.cursor()
        client.execute(
            f"""
        CREATE TABLE IF NOT EXISTS {DB_TABLE}
        (
            id UUID,
            film_uuid UUID,
            user_uuid UUID,
            message VARCHAR(500),
            value FLOAT,
            timestamp TIMESTAMP
        )
        ORDER BY timestamp;
        """
        )
        print(f"[Vertica] таблица {DB_TABLE} создана")


def load_data(idx_proc: int, total: int = 1000):
    faker = Faker()
    with vertica_python.connect(**connection_info) as conn:
        client = conn.cursor()

        data, leng = [], 0
        for _ in tqdm(range(total)):
            data.append(
                (
                    str(uuid.uuid4()),
                    str(uuid.uuid4()),
                    str(uuid.uuid4()),
                    faker.text(max_nb_chars=200).replace("\n", " "),
                    float(randint(1000, 20000)),
                    datetime.now(),
                )
            )
            leng += 1

            if leng >= BATCH_VERTICA:
                client.executemany(QUERY, data)
                data = []
                leng = 0

        if data:
            client.executemany(QUERY, data)
            data = []
            leng = 0

    print(f"Процесс {idx_proc} завершил запись в таблицу {DB_TABLE} в кол-ве {total}")


def main():
    create_table()

    processes = []
    for idx in tqdm(range(NUMBER_PROCESSES)):
        p = Process(target=load_data, args=(idx, NUMBER_RECORDS_PROCESS))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()


if __name__ == "__main__":
    try:
        start = time.perf_counter()
        main()
        end = time.perf_counter()
        print(
            f"Время заполнения {NUMBER_PROCESSES * NUMBER_RECORDS_PROCESS} \
                записей составило: {end - start:.2f} сек"
        )
    except vertica_python.errors.Error as err:
        print(f"Возникло исключение: {err}")
