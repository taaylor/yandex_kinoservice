import asyncio
import logging
from typing import NoReturn

from core.config import app_config
from db.postgres import get_session_context
from models.models import Notification
from services.processors.enricher import NotificationEnricher, get_notification_enricher
from services.processors.priority_manager import PriorityManager, get_priority_manager
from services.processors.sender import NotificationSender, get_notification_sender
from services.repository.notification_repository import (
    NotificationRepository,
    get_notification_repository,
)
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class NewNotificationProcessor:  # noqa: WPS214

    __slots__ = ("repository", "supplier", "enricher", "sender", "pr_manager")

    def __init__(
        self,
        repository: NotificationRepository,
        enricher: NotificationEnricher,
        sender: NotificationSender,
        pr_manager: PriorityManager,
    ) -> None:
        self.repository = repository
        self.enricher = enricher
        self.sender = sender
        self.pr_manager = pr_manager

    async def process_new_notifications(self) -> NoReturn:  # noqa: WPS210, WPS217
        while True:  # noqa: WPS457
            logger.info("Запущен процесс обработки нотификаций в статусе NEW")

            async with get_session_context() as session:
                while (
                    notifications := await self.repository.fetch_new_notifications(  # noqa: WPS332
                        session, limit=app_config.single_notify_batch
                    )
                ):

                    logger.info(f"Из БД получено: {len(notifications)} новых уведомлений")

                    enrich_failed_notifications, enriched_notifications = (
                        await self.enricher.enrich_notifications(notifications)
                    )

                    logger.info(
                        f"Получилось обогатить: {len(enriched_notifications)}, "
                        f"не нашлось профилей для: {len(enrich_failed_notifications)} уведомлений"
                    )

                    # Сортируем уведомления по времени отправки
                    send_now, send_later, sending_forbidden = (
                        await self.pr_manager.sort_by_priority(enriched_notifications)
                    )

                    await self._allocate_notifications(
                        session=session,
                        send_now=send_now,
                        send_later=send_later,
                        sending_forbidden=sending_forbidden,
                        processing_failed_notifications=enrich_failed_notifications,
                    )

            await asyncio.sleep(10)

    async def _allocate_notifications(
        self,
        session: AsyncSession,
        send_now: list[Notification],
        send_later: list[Notification],
        sending_forbidden: list[Notification],
        processing_failed_notifications: list[Notification],
    ):
        """Функция распределяет уведомления в зависимости от категории"""
        # Отправляем уведомления, которые можно отправить сейчас
        if send_now:
            await self.sender._push_to_queue(send_now)

        # Возвращаем в БД уведомления для отложенной отправки
        if send_later:
            await self.repository.update_notifications(session=session, notifications=send_later)
            logger.info(f"Уведомлений отложено для будущей отправки: {len(send_later)}")

        if sending_forbidden:
            await self.repository.update_notifications(
                session=session, notifications=sending_forbidden
            )
            logger.info(f"Уведомлений не разрешено отправлять: {len(sending_forbidden)}")
        # Устанавливаем статус "неудачно" для уведомлений, которые не удалось обогатить
        if processing_failed_notifications:
            await self.repository.update_notifications(
                session=session, notifications=processing_failed_notifications
            )
            logger.info(f"Уведомлений не удалось обогатить: {len(processing_failed_notifications)}")


def get_new_notification_processor() -> NewNotificationProcessor:
    repository = get_notification_repository()
    enricher = get_notification_enricher()
    sender = get_notification_sender()
    pr_manager = get_priority_manager()
    return NewNotificationProcessor(
        repository=repository, enricher=enricher, sender=sender, pr_manager=pr_manager
    )
