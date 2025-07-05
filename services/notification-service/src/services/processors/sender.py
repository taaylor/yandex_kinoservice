import asyncio
import logging

from models.models import Notification

logger = logging.getLogger(__name__)


class NotificationSender:

    __slots__ = ("queue_connector",)

    def __init__(self, queue_connector) -> None:
        self.queue_connector = queue_connector

    async def _push_to_queue(self, notifications: list[Notification]):
        """Функция отправляет уведомление в очередь отправки"""
        await asyncio.sleep(2)


def get_notification_sender() -> NotificationSender:
    return NotificationSender(queue_connector=None)
