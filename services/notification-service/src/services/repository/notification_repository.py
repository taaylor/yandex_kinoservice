import logging
from datetime import datetime
from functools import lru_cache
from uuid import UUID
from zoneinfo import ZoneInfo

from models.enums import MassNotificationStatus, NotificationStatus
from models.models import MassNotification, Notification
from services.repository.base_repository import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from utils.decorators import sqlalchemy_universal_decorator
from utils.serialization_utils import make_serializable

logger = logging.getLogger(__name__)


class NotificationRepository(BaseRepository[Notification | MassNotification]):  # noqa: WPS214

    @sqlalchemy_universal_decorator
    async def create_new_notification(
        self, session: AsyncSession, notification: Notification
    ) -> Notification:
        session.add(notification)
        await session.flush()
        return notification

    @sqlalchemy_universal_decorator
    async def fetch_new_notifications(
        self, session: AsyncSession, limit: int = 10
    ) -> list[Notification]:
        """Получает новые уведомления и сразу меняет их статус на PROCESSING"""
        stmt = (
            select(Notification)
            .where(Notification.status == NotificationStatus.NEW)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await session.execute(stmt)
        db_notifications = list(result.scalars().all())

        # Сразу меняем статус, чтобы другие процессы их не взяли
        for notify in db_notifications:
            notify.status = NotificationStatus.PROCESSING

        await session.flush()
        return db_notifications

    @sqlalchemy_universal_decorator
    async def fetch_delayed_notifications(
        self, session: AsyncSession, limit: int = 10
    ) -> list[Notification]:
        """Получает отложенные уведомления и сразу меняет их статус на PROCESSING"""
        db_notifications: list[Notification] = await self._get_delayed_notifications_list(
            session=session
        )  # type: ignore

        # Сразу меняем статус, чтобы другие процессы их не взяли
        for notify in db_notifications:
            notify.status = NotificationStatus.PROCESSING

        await session.flush()
        return db_notifications

    @sqlalchemy_universal_decorator
    async def update_notifications(  # noqa: WPS210
        self, session: AsyncSession, notifications: list[Notification]
    ) -> None:
        """Полностью обновляет уведомление в БД на то состояние, которое пришло в запросе"""
        notify_ids = [notify.id for notify in notifications]
        stmt = select(Notification).where(Notification.id.in_(notify_ids))
        result = await session.execute(stmt)
        db_notifications = result.scalars().all()

        notifications_dict = {notify.id: notify for notify in notifications}

        updated_count = 0
        for notify in db_notifications:
            updated_notify = notifications_dict[notify.id]
            for attr_name in updated_notify.__table__.columns.keys():
                if attr_name != "id":  # id не обновляем
                    setattr(notify, attr_name, getattr(updated_notify, attr_name))
            updated_count += 1

            # Принудительно помечаем JSON поле как измененное иначе sqlalchemy его не обновит
            flag_modified(notify, "event_data")
            # Костыль исправляет баг сериализации UUID в json
            # TODO: Исправить, использовать модель pydantic
            if "event_data" in notify.__dict__:
                setattr(notify, "event_data", make_serializable(notify.event_data))
        await session.flush()
        logger.info(f"Обновлено {updated_count} уведомлений")

    @sqlalchemy_universal_decorator
    async def update_notification_status_by_id(
        self, session: AsyncSession, notify_ids: list[UUID], status: NotificationStatus
    ) -> list[Notification]:
        """ "Обновляет статус уведомления в БД в результате обработки коллбека по отправке"""
        now_utc = datetime.now(ZoneInfo("UTC"))
        stmt = select(Notification).where(Notification.id.in_(notify_ids))
        result = await session.execute(stmt)
        db_notifications = list(result.scalars().all())

        for notify in db_notifications:
            notify.status = status
            notify.actual_sent_at = now_utc
        await session.flush()

        return db_notifications

    @sqlalchemy_universal_decorator
    async def fetch_mass_notification(
        self, session: AsyncSession, limit: int = 10
    ) -> list[MassNotification]:
        """Получает массовые уведомление и устанавливает им время начала отправки"""
        stmt = (
            select(MassNotification)
            .where(MassNotification.status == MassNotificationStatus.SENDING)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        notifications = list((await session.execute(stmt)).scalars().all())

        for notify in notifications:
            notify.start_sending_at = datetime.now(ZoneInfo("UTC"))
        await session.flush()
        return notifications

    @sqlalchemy_universal_decorator
    async def update_new_mass_notifications(
        self, session: AsyncSession, limit: int = 10
    ) -> tuple[int, int, int]:
        """Получает новые массовые уведомления и меняет их статус на SENDING или DELAYED"""
        now_utc = datetime.now(ZoneInfo("UTC"))
        stmt = (
            select(MassNotification)
            .where(MassNotification.status == MassNotificationStatus.NEW)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        db_notifications = list((await session.execute(stmt)).scalars().all())

        update_value = {"send": 0, "delay": 0}
        for notify in db_notifications:
            if notify.target_start_sending_at <= now_utc:
                notify.status = MassNotificationStatus.SENDING
                update_value["send"] += 1
            else:
                notify.status = MassNotificationStatus.DELAYED
                update_value["delay"] += 1
        await session.flush()
        return (len(db_notifications), update_value["send"], update_value["delay"])

    @sqlalchemy_universal_decorator
    async def update_delayed_mass_notifications(
        self, session: AsyncSession, limit: int = 10
    ) -> int:
        """Проверяет и обновляет массовые уведомления, которые были отложены"""
        db_notifications: list[MassNotification] = await self._get_delayed_notifications_list(
            session=session,
            mass_notification=True,
        )  # type: ignore

        for notify in db_notifications:
            notify.status = MassNotificationStatus.SENDING

        await session.flush()
        return len(db_notifications)

    async def _get_delayed_notifications_list(
        self,
        session: AsyncSession,
        limit: int = 10,
        mass_notification: bool = False,
    ) -> list[Notification | MassNotification]:
        """
        Извлекает отложенные уведомления из одной из двух моделей.

        :param session: AsyncSession для работы с БД.
        :param limit: Максимальное число записей для выборки.
        :param mass_notification:
            False — выбирает из Notification (по полю target_sent_at),
            True — из MassNotification (по полю target_start_sending_at).
        :return:
            Список экземпляров Notification или MassNotification,
            в зависимости от флага mass_notification.
        """
        if mass_notification:
            notification_model = MassNotification
            target_sent_at = MassNotification.target_start_sending_at
        else:
            notification_model = Notification
            target_sent_at = Notification.target_sent_at

        now_utc = datetime.now(ZoneInfo("UTC"))
        stmt = (
            select(notification_model)
            .where(
                notification_model.status == NotificationStatus.DELAYED,
                target_sent_at <= now_utc,
            )
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        executed_query = await session.execute(stmt)
        return list(executed_query.scalars().all())


@lru_cache
def get_notification_repository() -> NotificationRepository:
    return NotificationRepository()
