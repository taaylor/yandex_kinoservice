import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Callable

import aio_pika
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection
from aio_pika.exceptions import AMQPConnectionError
from aio_pika.pool import Pool
from aiohttp import web
from core.config import app_config

logger = logging.getLogger(__name__)


class AsyncMessageBroker(ABC):
    """Абстрактный класс для работы с брокером сообщений."""

    @abstractmethod
    async def consumer(self, queue_name: str, callback: Callable):
        """
        Метод позволяет прочитать сообщения из очереди, и выполнить их обработку
        :queue_name - название очереди
        :callback - функция обработки события
        """

    @abstractmethod
    async def close(self):
        """
        Метод позволяет закрыть все активные пулы соединений, каналов с брокером
        """


class RabbitMQConnector(AsyncMessageBroker):
    """Класс для работы с RabbitMQ, использует пул соединений и каналов для асинхронной работы"""

    __slots__ = ("hosts", "_channel_pool", "_connection_pool")

    auth_conf = {"login": app_config.rabbitmq.user, "password": app_config.rabbitmq.password}

    def __init__(self, hosts: list[str]):
        self.hosts = hosts
        self._channel_pool: AbstractRobustChannel = Pool(self._get_channel, max_size=2)
        self._connection_pool: AbstractRobustConnection = Pool(self._get_connection, max_size=2)

    async def _get_connection(self) -> AbstractRobustConnection:
        for host in self.hosts:
            try:
                connect = await aio_pika.connect_robust(host=host, **self.__class__.auth_conf)
                logger.debug(f"Установлено соединение с нодой {host=}")
                return connect
            except AMQPConnectionError as error:
                logger.error(
                    f"[RabbitMQ] Не удалось установить соединение с нодой {host} : {error=}"
                )
        logger.error("[RabbitMQ] Не удалось подключиться к rabbitmq")
        raise web.HTTPInternalServerError(text="Сервер немножко устал, повторите попытку позже")

    async def _get_channel(self) -> AbstractRobustChannel:
        async with self._connection_pool.acquire() as connection:
            channel = await connection.channel()
            logger.debug(f"Создан канал для соединения с {connection}")
            return channel

    async def consumer(self, queue_name: str, callback: Callable):
        async with self._channel_pool as channel:
            queue = await channel.declare_queue(queue_name, durable=True)
            while True:

                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        async with message.process():
                            await callback(message.body.decode())

                await asyncio.sleep(1)

    async def close(self):
        await self._channel_pool.close()
        await self._connection_pool.close()
        logger.info("Соединение с rabbitmq закрыто")
