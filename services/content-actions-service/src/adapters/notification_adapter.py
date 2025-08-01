import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx
from core.config import app_config
from models.logic_models import ReviewLikeNotify
from utils.http_decorators import EmptyServerResponse, handle_http_errors

logger = logging.getLogger(__name__)


class AbstractNotification(ABC):
    """Абстрактный класс для реализации отправки нотификации"""

    @abstractmethod
    async def send_review_liked_notify(self, notify) -> str:
        """Метод для создания нотификации"""


class NotificationAdapter(AbstractNotification):
    """
    Класс является адаптером для функционала отправки нотификациЙ.
    """

    async def send_review_liked_notify(self, notify: ReviewLikeNotify) -> str:
        """Метод создаёт нотификацию о лайке на комментарий пользователя пользователя"""
        logger.info(
            f"Получен запрос на отправку нотификации о лайке"
            f"на комментарий пользователя {notify.user_id}"
        )

        url = app_config.notification_api.get_notify_url
        logger.debug(f"Сформирована строка отправки нотификации: {url}")

        data = notify.model_dump(mode="json")
        logger.debug(f"Сформирована data отправки нотификации: {data}")

        return await self._send(url, data)

    @handle_http_errors(service_name=app_config.notification_api.host)
    async def _send(self, url: str, data: dict[str, Any]) -> str:
        """Отправляет запрос в сервис нотификаций"""
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(app_config.notification_api.timeout_sec)
        ) as client:

            response = await client.post(url=url, json=data)

            response.raise_for_status()

            if not response.content:
                logger.error(f"Пустой ответ от сервиса {app_config.notification_api.host}")
                raise EmptyServerResponse(
                    f"Получен пустой ответ от сервиса {app_config.notification_api.host}"
                )
            response_json = response.json()
            logger.debug(
                f"Получен ответ от сервиса {app_config.notification_api.host}: {response_json}"
            )

            return response_json.get("notification_id")


def get_notifier() -> NotificationAdapter:
    return NotificationAdapter()
