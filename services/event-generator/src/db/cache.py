import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Coroutine

from redis.asyncio import Redis
from utils.decorators import redis_handler_exceptions

logger = logging.getLogger(__name__)

cache_conn: Redis | None = None


class Cache(ABC):
    """Абстрактный класс для работы с кэшем."""

    @abstractmethod
    def get(self, key: str) -> Coroutine[None, None, str | None]:
        """Получает значение из кэша по ключу."""

    @abstractmethod
    def destroy(self, key: str) -> Coroutine[None, None, None]:
        """Удаляет значение из кэша по ключу."""

    @abstractmethod
    def destroy_all_by_pattern(self, pattern: str) -> Coroutine[None, None, int | None]:
        """Удаляет все значения из кэша по паттерну."""

    @abstractmethod
    def set(
        self, key: str, value: str, expire: int | None
    ) -> Coroutine[None, None, None]:  # noqa: WPS221
        """Сохраняет значение в кэш."""

    @abstractmethod
    def background_set(
        self, key: str, value: str, expire: int | None
    ) -> Coroutine[None, None, None]:
        """Сохраняет значение в кэш в фоновом режиме."""

    @abstractmethod
    def background_destroy(self, key: str) -> Coroutine[None, None, None]:
        """Удаляет значение из кэша в фоновом режиме."""

    @abstractmethod
    def background_destroy_all_by_pattern(self, pattern: str) -> Coroutine[None, None, None]:
        """Удаляет все значения из кэша по паттерну в фоновом режиме."""


class RedisCache(Cache):  # noqa: WPS214
    def __init__(self, redis: Redis):
        self.redis = redis

    @redis_handler_exceptions
    async def get(self, key: str) -> str | None:
        """Получает кеш из redis"""
        return await self.redis.get(key)

    @redis_handler_exceptions
    async def destroy(self, key: str) -> None:
        await self.redis.delete(key)
        logger.info(f"[RedisCache] Объект удален по ключу '{key}'")

    @redis_handler_exceptions
    async def set(self, key: str, value: str, expire: int | None):
        """Сохраняет кеш в redis"""
        await self.destroy(key)  # инвалидация кеша
        await self.redis.set(key, value, ex=expire)
        logger.info(f"[RedisCache] Объект сохранён в кэш по ключу '{key}'")

    @redis_handler_exceptions
    async def destroy_all_by_pattern(self, pattern: str) -> int:
        """
        Удаляет все ключи, соответствующие паттерну.
        Использует SCAN для безопасного поиска ключей.

        :param pattern: Паттерн для поиска ключей (например, "bookmarks:123:*")
        :return: Количество удаленных ключей
        """
        deleted_count = 0
        cursor = 0

        while True:
            # SCAN возвращает курсор и список ключей
            cursor, keys = await self.redis.scan(
                cursor=cursor, match=pattern, count=100
            )  # noqa: WPS221

            if keys:
                deleted_count += await self.redis.delete(*keys)
                logger.debug(f"Удалено {len(keys)} ключей по паттерну {pattern}")

            # Если курсор равен 0, мы прошли все ключи
            if cursor == 0:
                break

        logger.info(f"Всего удалено {deleted_count} ключей по паттерну {pattern}")
        return deleted_count

    async def background_set(self, key: str, value: str, expire: int | None):
        """Сохраняет кеш в фоновом процессе"""
        asyncio.create_task(self.set(key=key, value=value, expire=expire))
        logger.debug(f"Объект будет сохранен в кеш по {key=}")

    async def background_destroy(self, key: str) -> None:
        asyncio.create_task(self.destroy(key=key))
        logger.debug(f"Объект будет удален в кеше по {key=}")

    async def background_destroy_all_by_pattern(self, pattern: str) -> None:
        asyncio.create_task(self.destroy_all_by_pattern(pattern=pattern))
        logger.debug(f"Объекты будут удалены в кеше по {pattern=}")


def get_cache() -> Cache:
    if cache_conn is None:
        raise ValueError("Cache не инициализирован")
    return RedisCache(cache_conn)
