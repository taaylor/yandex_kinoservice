import logging
from functools import lru_cache
from typing import Any

import backoff
import httpx
from aiochclient import ChClient, Record, exceptions
from core.config import app_config
from db.abstract import DBAbstract

logger = logging.getLogger(__name__)


class ClickHouseConnector(DBAbstract):

    # ClickHouse работает, на сессии клиента httpx
    client_httpx: httpx.AsyncClient | None = None

    def __init__(self):
        self._client_ch: ChClient | None = None

    @classmethod
    async def close(cls) -> None:
        if cls.client_httpx:
            await cls.client_httpx.aclose()
        cls.client_httpx = None

    @backoff.on_exception(
        backoff.expo,
        (httpx.ConnectError, httpx.ConnectTimeout, exceptions.ChClientError),
        max_tries=3,
        jitter=backoff.full_jitter,
    )
    async def fetch(self, query: str, *args, **kwargs) -> list[Record] | None:
        client = await self._get_client()
        try:
            logger.debug(f"Начинаю выполнять запрос: {query}")
            result = await client.fetch(query, *args, **kwargs)
            return result
        except exceptions.ChClientError as error:
            logger.error(f"Произошла ошибка при выполнении запроса: {error}")
            return None

    @property
    def _settings_ch(self) -> dict[str, Any]:
        return {
            "url": app_config.clickhouse.url,
            "user": app_config.clickhouse.user,
            "password": app_config.clickhouse.password,
            "database": app_config.clickhouse.database,
        }

    async def _get_client(self) -> ChClient:
        if self._client_ch is None:
            self._client_ch = await self._create_client()
        return self._client_ch

    @backoff.on_exception(
        backoff.expo,
        (httpx.ConnectError, httpx.ConnectTimeout, exceptions.ChClientError),
        max_tries=3,
        jitter=backoff.full_jitter,
    )
    async def _create_client(self) -> ChClient:
        client_ch = ChClient(session=self.__class__.client_httpx, **self._settings_ch)
        if await client_ch.is_alive():
            logger.info("Успешное подключение к ClickHouse")
            return client_ch
        logger.error("Не удалось установить соединения с ClickHouse")
        raise httpx.ConnectError("Не удалось установить соединения с ClickHouse")


@lru_cache
def get_chclient() -> DBAbstract:
    return ClickHouseConnector()
