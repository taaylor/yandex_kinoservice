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
