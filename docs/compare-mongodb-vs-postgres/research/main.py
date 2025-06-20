from contextlib import closing

import psycopg
from core import config
from psycopg import ClientCursor
from psycopg.rows import dict_row

dsl = {
    'dbname': config.POSTGRES_DB,
    'user': config.POSTGRES_USER,
    'password': config.POSTGRES_PASSWORD,
    'host': config.POSTGRES_HOST,
    'port': config.POSTGRES_PORT,
}

if __name__ == '__main__':
    # es = get_elasticsearch(settings.ELASTICSEARCH_HOST)
    # storage = JsonFileStorage('state.json')
    # state = State(storage)
    with psycopg.connect(
        **dsl,
        row_factory=dict_row,
        cursor_factory=ClientCursor
    ) as pg_conn:
        while True:
            with closing(pg_conn.cursor(row_factory=dict_row)) as cursor:
                pass
