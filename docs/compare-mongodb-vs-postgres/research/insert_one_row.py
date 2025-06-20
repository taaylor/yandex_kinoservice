# import uuid
# from datetime import datetime

# import psycopg

# # DSN: подставьте свои параметры при необходимости
# # DSN = "postgresql://postgres:postgres@postgres:5432/pg_db"
# DSN = "postgresql://postgres:postgres@localhost:5432/pg_db"

# def insert_one_rating():
#     # Генерируем значения
#     new_id = uuid.uuid4()
#     user_id = uuid.uuid4()
#     film_id = uuid.uuid4()
#     now = datetime.now()
#     score = 5  # пример оценки от 1 до 10

#     with psycopg.connect(DSN) as conn:
#         with conn.cursor() as cur:
#             cur.execute(
#                 """
#                 INSERT INTO rating (id, user_id, film_id, created_at, updated_at, score)
#                 VALUES (%s, %s, %s, %s, %s, %s)
#                 ON CONFLICT (film_id, user_id) DO NOTHING
#                 """,
#                 (new_id, user_id, film_id, now, now, score)
#             )
#             # при выходе из with conn.cursor() и with psycopg.connect() транзакция зафиксируется автоматически

# if __name__ == "__main__":
#     insert_one_rating()
#     print("Вставка одной записи выполнена")

import asyncio
import random
import uuid
from datetime import datetime
from string import printable

import asyncpg

DSN = "postgresql://postgres:postgres@localhost:5432/pg_db"
BATCH_SIZE = 100_000  # 100 тыс.

COUNT_RECORDS = 10_000_000  # 10 млн.

COUNT_BATCHES = COUNT_RECORDS // BATCH_SIZE

EXTRA_FIELDS = {
    "score": lambda: random.randint(1, 10),
    "comment": lambda: printable,
}

user_ids = [uuid.uuid4() for _ in range(COUNT_BATCHES // 10)]
film_ids = [uuid.uuid4() for _ in range(COUNT_BATCHES // 10)]


def get_pair_user_id_film_id(film_ids, user_ids):
    yield from (
        (f_id, u_id,)
        for f_id in film_ids
        for u_id in user_ids
    )


async def insert_one_rating():
    # new_id = uuid.uuid4()
    # user_id = uuid.uuid4()
    # film_id = uuid.uuid4()
    # now = datetime.now()
    # score = 5
    sql = """
    INSERT INTO rating (id, user_id, film_id, created_at, updated_at, score)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (film_id, user_id) DO NOTHING
    """
    # pool = await asyncpg.create_pool(DSN)
    async with asyncpg.create_pool(
        dsn=DSN,
        min_size=1,
        max_size=10
    ) as pool:
        async with pool.acquire() as conn:
            for _ in range(COUNT_BATCHES):
                batch = []
                for counter in range(1, BATCH_SIZE + 1):
                    batch.append(
                        (
                            uuid.uuid4(),
                            uuid.uuid4(),
                            uuid.uuid4(),
                            datetime.now(),
                            datetime.now(),
                            random.randint(1, 10),
                        )
                    )
            # await conn.execute(
            #     """
            #     INSERT INTO rating (id, user_id, film_id, created_at, updated_at, score)
            #     VALUES ($1, $2, $3, $4, $5, $6)
            #     ON CONFLICT (film_id, user_id) DO NOTHING
            #     """,
            #     new_id, user_id, film_id, now, now, score
            # )
                await conn.executemany(
                    sql,
                    batch
                )
            # print("lalala")
    # await pool.close()

if __name__ == "__main__":
    asyncio.run(insert_one_rating())
    print("Вставка одной записи выполнена")
