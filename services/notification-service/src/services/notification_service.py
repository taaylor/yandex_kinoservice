import logging
from functools import lru_cache

from api.v1.notification.schemas import SingleNotificationRequest, SingleNotificationResponse
from db.postgres import get_session
from fastapi import Depends, HTTPException, status
from models.models import Notification
from services.base_service import BaseService
from services.repository.notification_repository import (
    NotificationRepository,
    get_notification_repository,
)
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class NotificationService(BaseService):

    async def send_single_notification(
        self, request_body: SingleNotificationRequest
    ) -> SingleNotificationResponse:

        logger.info(
            f"Получен запрос на отправку нотификации: {request_body.model_dump_json(indent=4)}"
        )

        new_notify = Notification(
            user_id=request_body.user_id,
            method=request_body.method,
            source=request_body.source,
            target_sent_at=request_body.target_sent_at,
            priority=request_body.priority,
            event_type=request_body.event_type,
            event_data=request_body.event_data,
        )

        crated_notify = await self.repository.create_new_notification(
            self.session, notification=new_notify
        )

        if crated_notify:

            logger.info(f"Сохранён запрос на уведомление {crated_notify.id}")

            return SingleNotificationResponse(notification_id=crated_notify.id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось сохранить уведомление",
        )


@lru_cache
def get_notification_service(
    repository: NotificationRepository = Depends(get_notification_repository),
    session: AsyncSession = Depends(get_session),
) -> NotificationService:
    return NotificationService(repository=repository, session=session)
