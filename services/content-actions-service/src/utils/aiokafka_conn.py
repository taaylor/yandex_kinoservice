import json
import logging
from abc import ABC, abstractmethod
from typing import Any

import backoff
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError, KafkaError, KafkaTimeoutError
from core.config import app_config

logger = logging.getLogger(__name__)


class AIOMessageBroker(ABC):

    @abstractmethod
    async def push_message(*args, **kwargs) -> bool:
        """Отправляет сообщение в брокер"""

    @abstractmethod
    async def connect(*args, **kwargs) -> None:
        """Устанавливает соединение с брокером сообщений"""

    async def disconnect(*args, **kwargs) -> None:
        """Закрывает соединение с брокером сообщений"""


class AIOKafkaConnector(AIOMessageBroker):  # noqa: WPS338

    __slots__ = ("_producer",)

    @staticmethod
    def _json_serializer(value: Any) -> bytes:  # noqa: WPS602
        """Сериализация значений в JSON"""
        if isinstance(value, (str, bytes)):
            return value.encode("utf-8") if isinstance(value, str) else value
        return json.dumps(value, ensure_ascii=False).encode("utf-8")

    def __init__(self):
        self._producer: AIOKafkaProducer | None = None

    @property
    def _kafka_config(self) -> dict[str, Any]:
        config = app_config.kafka
        return {
            "bootstrap_servers": config.get_servers,
            "client_id": app_config.project_name,
            "value_serializer": self._json_serializer,
            "key_serializer": lambda v: (
                str(v).encode("utf-8") if v is not None else None  # noqa: WPS504
            ),
            "retry_backoff_ms": config.retry_backoff_ms,
            "request_timeout_ms": config.request_timeout_ms,
            "linger_ms": config.linger_ms,
            "security_protocol": config.security_protocol,
        }

    @backoff.on_exception(
        backoff.expo,
        (KafkaTimeoutError, KafkaConnectionError),
        max_tries=5,
        jitter=backoff.full_jitter,
        max_time=60,
    )
    async def push_message(  # noqa: WPS211
        self,
        topic: str,
        value: Any,
        key: str | bytes | None = None,
        partition: int | None = None,
        timestamp_ms: int | None = None,
        headers: str | bytes | None = None,
    ) -> bool:
        try:
            if producer := self._producer:  # noqa: WPS332
                result = await producer.send_and_wait(
                    topic=topic,
                    value=value,
                    partition=partition,
                    key=key,
                    timestamp_ms=timestamp_ms,
                    headers=headers,
                )
                if res := bool(result):  # noqa: WPS332
                    logger.info(f"Событие было успешно отправлено в {topic=}")
                return res
            logger.error(f"Продюсер не был инициализирован, при отправке события в {topic=}")
            return False
        except KafkaError as error:
            logger.error(f"Возникла ошибка при работе с Kafka: {error}")
            return False

    @backoff.on_exception(
        backoff.expo,
        (KafkaTimeoutError, KafkaConnectionError),
        max_tries=5,
        jitter=backoff.full_jitter,
        max_time=60,
    )
    async def connect(self):
        try:
            producer = self._get_or_create_producer()
            await producer.start()
            logger.info("Соедниение с Kafka успешно установлено")
        except (KafkaTimeoutError, KafkaConnectionError) as error:
            logger.error(f"Не удалось подключиться к Kafka после 5 попыток: {error}")
            self.producer = None
        except KafkaError as error:
            logger.error(f"Возникла ошибка при подключении к Kafka: {error}")
            self.producer = None

    async def disconnect(self):
        if self._producer:
            await self._producer.stop()
            self._producer = None

    def _get_or_create_producer(self) -> AIOKafkaProducer:
        if self._producer is None:
            self._producer = AIOKafkaProducer(**self._kafka_config)
        return self._producer


_kafka_connector: AIOKafkaConnector | None = None


def get_broker_connector() -> AIOMessageBroker:
    global _kafka_connector  # noqa: WPS420
    if _kafka_connector is None:
        _kafka_connector = AIOKafkaConnector()  # noqa: WPS122
    return _kafka_connector  # noqa: WPS121
