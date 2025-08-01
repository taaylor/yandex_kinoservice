import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Protocol, Self

import backoff
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import ConsumerStoppedError, KafkaConnectionError, KafkaTimeoutError
from core.config import app_config

logger = logging.getLogger(__name__)


class MessageHandler(Protocol):
    """Протокол для обработчика сообщений Kafka."""

    async def __call__(self, topic: str, message: bytes) -> None:
        """Обработать сообщение из Kafka.

        Args:
            topic: Название топика
            message: Тело сообщения
        """
        ...


class KafkaConsumerManager:  # noqa: WPS214
    """Менеджер для управления Kafka консюмером с улучшенной обработкой ошибок."""

    def __init__(
        self,
        topics: list[str],
        group_id: str,
        bootstrap_servers: list[str] | None = None,
        **consumer_kwargs,
    ):
        self._topics = topics
        self._group_id = group_id
        self._bootstrap_servers = bootstrap_servers or app_config.kafka.get_servers
        self._consumer_kwargs = consumer_kwargs
        self._consumer: AIOKafkaConsumer | None = None
        self._is_running = False

    @backoff.on_exception(
        backoff.expo,
        (KafkaConnectionError, KafkaTimeoutError, OSError),
        max_time=300,
        factor=2,
        jitter=backoff.full_jitter,
    )
    async def start(self) -> None:
        """Запустить Kafka консюмер с повторными попытками."""
        if self._consumer is not None:
            logger.warning("Consumer уже запущен")
            return

        logger.info(
            f"Запуск Kafka consumer для топиков: {self._topics}, "
            f"group_id: {self._group_id}, "
            f"servers: {self._bootstrap_servers}"
        )

        self._consumer = self._create_consumer()
        await self._consumer.start()
        self._is_running = True
        logger.info("Kafka consumer успешно запущен")

    async def stop(self) -> None:
        """Остановить Kafka консюмер."""
        if not self._is_running or self._consumer is None:
            logger.info("Consumer не запущен или уже остановлен")
            return

        logger.info("Остановка Kafka consumer...")
        self._is_running = False

        try:
            await self._consumer.stop()
            logger.info("Kafka consumer успешно остановлен")
        except Exception as e:
            logger.error(f"Ошибка при остановке consumer: {e}")
        finally:
            self._consumer = None

    async def consume_messages(  # noqa: WPS210, WPS213, WPS231, WPS220
        self,
        message_handler: MessageHandler,
        max_messages_per_batch: int = 100,
    ) -> None:
        """Потреблять сообщения из Kafka.

        Args:
            message_handler: Функция для обработки сообщений
            max_messages_per_batch: Максимальное количество сообщений в батче
        """
        if not self._is_running or self._consumer is None:
            raise RuntimeError("Consumer не запущен. Вызовите start() сначала.")

        logger.info("Начало потребления сообщений...")
        # TODO: Разбить код ниже на несколько функций.
        try:
            while self._is_running:
                try:  # noqa: WPS505
                    message_batch = await self._consumer.getmany(
                        timeout_ms=10000, max_records=max_messages_per_batch
                    )

                    if not message_batch:
                        continue  # noqa: WPS220

                    # Обрабатываем все сообщения в батче
                    tasks = []
                    for topic_partition, messages in message_batch.items():
                        for message in messages:  # noqa: WPS220
                            if message.value is not None:  # noqa: WPS220
                                task = self._safe_message_handler(  # noqa: WPS220
                                    message_handler, message.topic, message.value
                                )
                                tasks.append(task)  # noqa: WPS220

                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)  # noqa: WPS220
                        logger.debug(f"Обработано {len(tasks)} сообщений")  # noqa: WPS220

                except ConsumerStoppedError:
                    logger.info("Consumer был остановлен")
                    break
                except (KafkaConnectionError, KafkaTimeoutError) as e:
                    logger.error(f"Ошибка подключения к Kafka: {e}")
                    # Попытка переподключения через backoff
                    await asyncio.sleep(5)
                    continue
                except Exception as e:
                    logger.error(f"Неожиданная ошибка при потреблении: {e}", exc_info=True)
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("Потребление сообщений было отменено")
        finally:
            logger.info("Завершение потребления сообщений")

    @asynccontextmanager
    async def consumer_context(self) -> AsyncGenerator[Self, Any]:
        """Контекстный менеджер для автоматического управления жизненным циклом консюмера."""
        try:
            await self.start()
            yield self
        finally:
            await self.stop()

    @property
    def is_running(self) -> bool:
        """Проверить, запущен ли консюмер."""
        return self._is_running

    async def _safe_message_handler(
        self, message_handler: MessageHandler, topic: str, message: bytes
    ) -> None:
        """Безопасно обработать сообщение с логированием ошибок."""
        try:
            await message_handler(topic, message)
        except Exception as e:
            logger.error(
                f"Ошибка при обработке сообщения из топика {topic}: {e}",
                exc_info=True,
            )

    def _create_consumer(self) -> AIOKafkaConsumer:
        """Создать экземпляр Kafka консюмера."""
        # Преобразуем список серверов в строку, если нужно

        return AIOKafkaConsumer(
            *self._topics,
            bootstrap_servers=self._bootstrap_servers,  # type: ignore
            group_id=self._group_id,
            enable_auto_commit=True,
            auto_commit_interval_ms=5000,
            auto_offset_reset="earliest",
            session_timeout_ms=60000,
            heartbeat_interval_ms=20000,
            max_poll_interval_ms=300000,
            request_timeout_ms=app_config.kafka.request_timeout_ms,
            retry_backoff_ms=app_config.kafka.retry_backoff_ms,
            security_protocol=app_config.kafka.security_protocol,
        )


def create_consumer_manager(
    topics: list[str] | None = None,
    group_id: str | None = None,
    bootstrap_servers: list[str] | None = None,
) -> KafkaConsumerManager:
    """Создать Kafka консюмер для recs-profile сервиса.

    Args:
        topics: Список топиков для подписки. По умолчанию из конфигурации.
        group_id: ID группы консюмеров. По умолчанию из названия проекта.
        bootstrap_servers: Список Kafka серверов. По умолчанию из конфигурации.

    Returns:
        Настроенный экземпляр KafkaConsumerManager
    """
    if topics is None:
        topics = [
            app_config.kafka.rec_bookmarks_list_topic,
            app_config.kafka.rec_user_ratings_films_topic,
        ]
    if group_id is None:
        group_id = f"{app_config.project_name}-consumer-group"

    return KafkaConsumerManager(
        topics=topics,
        group_id=group_id,
        bootstrap_servers=bootstrap_servers,
    )
