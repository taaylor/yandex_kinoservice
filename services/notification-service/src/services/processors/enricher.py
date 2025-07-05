import logging
from uuid import UUID

from models.enums import EventType, NotificationStatus
from models.logic_models import UserProfile
from models.models import Notification
from suppliers.user_profile_supplier import ProfileSupplier, get_profile_supplier

logger = logging.getLogger(__name__)


class NotificationEnricher:  # noqa: WPS214
    """Обогащает экземпляры уведомлений дополнительными атрибутами
    для отправки персональных уведомлений"""

    # TODO: Добавить разное обогащение для разных типов уведомлений

    __slots__ = ("supplier",)

    def __init__(self, supplier: ProfileSupplier) -> None:
        self.supplier = supplier

    async def enrich_notifications(  # noqa: WPS210, WPS213, WPS231
        self, notifications: list[Notification]
    ) -> tuple[list[Notification], list[Notification]]:
        enriched_notifications: list[Notification] = []
        enrich_failed_notifications: list[Notification] = []

        test_type, film_review_liked_type, user_registered_type, mass_type = (
            await self._sort_notifications_by_type(notifications)
        )

        if test_type:
            logger.info(f"Получено: {len(test_type)} test_type уведомлений для обогащения")
            failed, enriched = await self._enrich_test_notify(test_type)
            if enriched:
                enriched_notifications.extend(enriched)
            if failed:
                enrich_failed_notifications.extend(failed)

        if film_review_liked_type:
            logger.info(
                f"Получено: {len(film_review_liked_type)}"
                f"film_review_liked_type уведомлений для обогащения"
            )
            enriched, failed = await self._enrich_film_review_liked_notify(test_type)
            if enriched:
                enriched_notifications.extend(enriched)
            if failed:
                enrich_failed_notifications.extend(failed)

        if user_registered_type:
            logger.info(
                f"Получено: {len(user_registered_type)}"
                f"user_registered_type уведомлений для обогащения"
            )
            enriched, failed = await self._enrich_user_registered_notify(test_type)
            if enriched:
                enriched_notifications.extend(enriched)
            if failed:
                enrich_failed_notifications.extend(failed)

        if mass_type:
            logger.info(f"Получено: {len(test_type)} mass_type уведомлений для обогащения")
            enriched, failed = await self._enrich_mass_notify(test_type)
            if enriched:
                enriched_notifications.extend(enriched)
            if failed:
                enrich_failed_notifications.extend(failed)

        return enrich_failed_notifications, enriched_notifications

    async def _fetch_profiles(self, user_ids: set[UUID]) -> list[UserProfile]:
        try:
            profiles = await self.supplier.fetch_profiles(user_ids=user_ids)
            logger.debug(f"Получено: {len(profiles)} профилей для отправки уведомлений")
            return profiles
        except Exception:
            logger.warning(f"Не удалось получить профили для: {user_ids}")
            return []

    async def _sort_notifications_by_type(  # noqa: WPS231
        self, notifications: list[Notification]
    ) -> tuple[
        list[Notification], list[Notification], list[Notification], list[Notification]
    ]:  # noqa: WPS221
        test_type = []
        film_review_liked_type = []
        user_registered_type = []
        mass_type = []

        for notify in notifications:
            if notify.event_type == EventType.TEST:
                test_type.append(notify)
            elif notify.event_type == EventType.USER_REVIEW_LIKED:
                film_review_liked_type.append(notify)
            elif notify.event_type == EventType.USER_REGISTERED:
                user_registered_type.append(notify)
            elif notify.event_type == EventType.MASS_NOTIFY:
                mass_type.append(notify)
            else:
                logger.warning(
                    f"Поступило уведомление: {notify.id} с неизвестным типом: {notify.event_type}"
                )

        return test_type, film_review_liked_type, user_registered_type, mass_type  # noqa: WPS210

    async def _enrich_test_notify(  # noqa: WPS210
        self, notifications: list[Notification]
    ) -> tuple[list[Notification], list[Notification]]:
        enriched_notifications: list[Notification] = []
        enrich_failed_notifications: list[Notification] = []

        user_ids = {notification.user_id for notification in notifications}
        profiles = await self._fetch_profiles(user_ids)

        # Преобразую в dict чтобы сложность сопоставления нотификации и
        # профиля была O(m + n), а не O(m * n) (т.к. перебор двух списков отстой)
        profiles_dict = {profile.user_id: profile for profile in profiles}

        for notify in notifications:
            user_profile = profiles_dict.get(notify.user_id)

            if not user_profile:
                logger.warning(f"Не удалось обогатить нотификацию {notify.id}")
                notify.status = NotificationStatus.PROCESSING_ERROR
                enrich_failed_notifications.append(notify)
                continue

            notify.user_timezone = user_profile.user_timezone
            notify.event_data.update(
                {
                    "first_name": user_profile.first_name,
                    "last_name": user_profile.last_name,
                    "gender": user_profile.gender,
                    "email": user_profile.email,
                    "is_fictional_email": user_profile.is_fictional_email,
                    "is_email_notify_allowed": user_profile.is_email_notify_allowed,
                    "is_verified_email": user_profile.is_verified_email,
                    "created_at": user_profile.is_verified_email,
                }
            )

            enriched_notifications.append(notify)
        return enrich_failed_notifications, enriched_notifications

    async def _enrich_film_review_liked_notify(  # noqa: WPS210
        self, notifications: list[Notification]
    ) -> tuple[list[Notification], list[Notification]]:
        enriched_notifications: list[Notification] = []
        enrich_failed_notifications: list[Notification] = []

        user_ids = {notification.user_id for notification in notifications}
        # liked_by_user_ids = {
        #     notification.event_data["liked_by_user_id"] for notification in notifications
        # }
        # review_ids = {notification.event_data["review_id"] for notification in notifications}
        # film_ids = {notification.event_data["film_id"] for notification in notifications}
        profiles = await self._fetch_profiles(user_ids)

        # Преобразую в dict чтобы сложность сопоставления нотификации и
        # профиля была O(m + n), а не O(m * n) (т.к. перебор двух списков отстой)
        profiles_dict = {profile.user_id: profile for profile in profiles}

        for notify in notifications:
            user_profile = profiles_dict.get(notify.user_id)

            if not user_profile:
                logger.warning(f"Не удалось обогатить нотификацию {notify.id}")
                notify.status = NotificationStatus.PROCESSING_ERROR
                enrich_failed_notifications.append(notify)
                continue

            notify.user_timezone = user_profile.user_timezone
            notify.event_data.update(
                {
                    "first_name": user_profile.first_name,
                    "last_name": user_profile.last_name,
                    "gender": user_profile.gender,
                    "email": user_profile.email,
                    "is_fictional_email": user_profile.is_fictional_email,
                    "is_email_notify_allowed": user_profile.is_email_notify_allowed,
                    "is_verified_email": user_profile.is_verified_email,
                    "created_at": user_profile.is_verified_email,
                }
            )

            enriched_notifications.append(notify)
        return enrich_failed_notifications, enriched_notifications

    async def _enrich_user_registered_notify(  # noqa: WPS210
        self, notifications: list[Notification]
    ) -> tuple[list[Notification], list[Notification]]:
        enriched_notifications: list[Notification] = []
        enrich_failed_notifications: list[Notification] = []

        user_ids = {notification.user_id for notification in notifications}
        profiles = await self._fetch_profiles(user_ids)

        # Преобразую в dict чтобы сложность сопоставления нотификации и
        # профиля была O(m + n), а не O(m * n) (т.к. перебор двух списков отстой)
        profiles_dict = {profile.user_id: profile for profile in profiles}

        for notify in notifications:
            user_profile = profiles_dict.get(notify.user_id)

            if not user_profile:
                logger.warning(f"Не удалось обогатить нотификацию {notify.id}")
                notify.status = NotificationStatus.PROCESSING_ERROR
                enrich_failed_notifications.append(notify)
                continue

            notify.user_timezone = user_profile.user_timezone
            notify.event_data.update(
                {
                    "first_name": user_profile.first_name,
                    "last_name": user_profile.last_name,
                    "gender": user_profile.gender,
                    "email": user_profile.email,
                    "is_fictional_email": user_profile.is_fictional_email,
                    "is_email_notify_allowed": user_profile.is_email_notify_allowed,
                    "is_verified_email": user_profile.is_verified_email,
                    "created_at": user_profile.is_verified_email,
                }
            )

            enriched_notifications.append(notify)
        return enrich_failed_notifications, enriched_notifications

    async def _enrich_mass_notify(  # noqa: WPS210
        self, notifications: list[Notification]
    ) -> tuple[list[Notification], list[Notification]]:
        enriched_notifications: list[Notification] = []
        enrich_failed_notifications: list[Notification] = []

        user_ids = {notification.user_id for notification in notifications}
        profiles = await self._fetch_profiles(user_ids)

        # Преобразую в dict чтобы сложность сопоставления нотификации и
        # профиля была O(m + n), а не O(m * n) (т.к. перебор двух списков отстой)
        profiles_dict = {profile.user_id: profile for profile in profiles}

        for notify in notifications:
            user_profile = profiles_dict.get(notify.user_id)

            if not user_profile:
                logger.warning(f"Не удалось обогатить нотификацию {notify.id}")
                notify.status = NotificationStatus.PROCESSING_ERROR
                enrich_failed_notifications.append(notify)
                continue

            notify.user_timezone = user_profile.user_timezone
            notify.event_data.update(
                {
                    "first_name": user_profile.first_name,
                    "last_name": user_profile.last_name,
                    "gender": user_profile.gender,
                    "email": user_profile.email,
                    "is_fictional_email": user_profile.is_fictional_email,
                    "is_email_notify_allowed": user_profile.is_email_notify_allowed,
                    "is_verified_email": user_profile.is_verified_email,
                    "created_at": user_profile.is_verified_email,
                }
            )

            enriched_notifications.append(notify)
        return enrich_failed_notifications, enriched_notifications


def get_notification_enricher() -> NotificationEnricher:
    supplier = get_profile_supplier()
    return NotificationEnricher(supplier=supplier)
