import logging
import os
import sys

from clickhouse_driver import Client, errors
from dotenv import find_dotenv, load_dotenv


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.hasHandlers():
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger


logger = get_logger(__name__)


load_dotenv(find_dotenv())

CLICKHOUSE_HOST = os.getenv("CLK_HOST")
PASSWORD = os.getenv("CLK_DEFAULT_PASSWORD")
TABLE_NAME = "metrics"
TABLE_NAME_DIST = "metrics_dst"
DB_NAME = "kinoservice"
CLUSTER_NAME = "kinoservice_cluster"


def main():
    client = Client(CLICKHOUSE_HOST, user="default", password=PASSWORD)

    # Создание базы данных
    client.execute(
        """
        CREATE DATABASE IF NOT EXISTS {DB_NAME}
        ON CLUSTER {CLUSTER_NAME}
    """.format(
            DB_NAME=DB_NAME, CLUSTER_NAME=CLUSTER_NAME
        )
    )

    # Создание локальной таблицы с репликацией
    client.execute(
        """
        CREATE TABLE IF NOT EXISTS {DB_NAME}.{TABLE_NAME}
        ON CLUSTER {CLUSTER_NAME}
        (
            id Int64 DEFAULT generateUUIDv4(),
            user_session Nullable(UUID),
            user_uuid Nullable(UUID),
            ip_address Nullable(String),
            film_uuid Nullable(UUID),
            event_params Map(String, String),
            event_type String,
            message_event String,
            event_timestamp DateTime,
            user_timestamp DateTime
        )
        ENGINE = ReplicatedMergeTree(
            '/clickhouse/tables/{cluster}/{shard}/{TABLE_NAME}',
            '{replica}'
        )
        PARTITION BY toYYYYMMDD(event_timestamp)
        ORDER BY event_timestamp
        TTL event_timestamp + INTERVAL 360 DAY
        SETTINGS index_granularity = 8192
    """.format(
            DB_NAME=DB_NAME,
            TABLE_NAME=TABLE_NAME,
            CLUSTER_NAME=CLUSTER_NAME,
            cluster="{cluster}",
            shard="{shard}",
            replica="{replica}",
        )
    )

    # Создание дистрибутивной таблицы
    client.execute(
        """
        CREATE TABLE IF NOT EXISTS {DB_NAME}.{TABLE_NAME_DIST}
        ON CLUSTER {CLUSTER_NAME}
        (
            id Int64 DEFAULT generateUUIDv4(),
            user_session Nullable(UUID),
            user_uuid Nullable(UUID),
            ip_address Nullable(String),
            film_uuid Nullable(UUID),
            event_params Map(String, String),
            event_type String,
            message_event String,
            event_timestamp DateTime,
            user_timestamp DateTime
        )
        ENGINE = Distributed(
            '{CLUSTER_NAME}',
            '{DB_NAME}',
            '{TABLE_NAME}',
            rand()
        )
    """.format(
            DB_NAME=DB_NAME,
            TABLE_NAME_DIST=TABLE_NAME_DIST,
            CLUSTER_NAME=CLUSTER_NAME,
            TABLE_NAME=TABLE_NAME,
        )
    )


if __name__ == "__main__":
    try:
        main()
        logger.info("Dump базы данных выполнен успешно!")
    except errors.Error as error:
        logger.error(f"Возникло исключение: {error}")
