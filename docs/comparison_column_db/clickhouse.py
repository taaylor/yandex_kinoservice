import time
import uuid
from datetime import datetime
from multiprocessing import Process
from random import randint

from clickhouse_driver import Client, errors
from faker import Faker
from tqdm import tqdm

DB_TABLE = "default.test"
NUMBER_PROCESSES = 5
NUMBER_RECORDS_PROCESS = 1_000_000
BATCH_CLICKHOUSE = 1000
QUERY = """
    INSERT INTO default.test
    (film_uuid, user_uuid, message, value, timestamp)
    VALUES
    """


def create_table():
    client = Client("localhost")
    client.execute(
        f"""
    CREATE TABLE IF NOT EXISTS {DB_TABLE}
    (
        id UUID DEFAULT generateUUIDv4(),
        film_uuid UUID,
        user_uuid UUID,
        message String,
        value Float64,
        timestamp DateTime DEFAULT now()
    )
    ENGINE = MergeTree()
    ORDER BY timestamp;
    """
    )
    print("[ClickHouse] таблица default.test создана")
    client.disconnect()


def load_data(idx_proc: int, total: int = 1000):
    client = Client("localhost")
    faker = Faker()

    data, leng = [], 0
    for _ in tqdm(range(total)):
        data.append(
            (
                uuid.uuid4(),
                uuid.uuid4(),
                faker.text(max_nb_chars=200).replace("\n", " ").replace("\r", ""),
                float(randint(1000, 20000)),
                datetime.now(),
            )
        )
        leng += 1

        if leng >= BATCH_CLICKHOUSE:
            client.execute(QUERY, data)
            data = []
            leng = 0

    if data:
        client.execute(QUERY, data)
        data = []
        leng = 0

    client.disconnect()
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
    except errors.Error as err:
        print(f"Возникло исключение: {err}")
