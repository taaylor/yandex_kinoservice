import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from core.config import app_config
from models.enums import NotificationMethod, NotificationStatus, Priority
from models.models import Notification

logger = logging.getLogger(__name__)


class PriorityManager:

    async def sort_by_priority(  # noqa: WPS210, WPS231
        self, notifications: list[Notification]
    ) -> tuple[list[Notification], list[Notification], list[Notification]]:
        """
        Функция проверяет необходимость отправки уведомления прямо сейчас.
        Возвращает кортеж: (уведомления для отправки сейчас, уведомления для отложенной отправки,
        уведомления, которые не разрешено отправлять)
        """
        send_now = []
        send_later = []
        sending_forbidden = []

        # Интервал отправки: с notify_start_hour до notify_end_hour по времени пользователя
        start_hour = app_config.notify_start_hour
        end_hour = app_config.notify_end_hour

        for notify in notifications:
            if notify.priority == Priority.HIGH:
                # Высокоприоритетные уведомления отправляем сразу
                send_now.append(notify)
                continue

            if notify.method == NotificationMethod.EMAIL:
                if not notify.event_data.get("is_email_notify_allowed"):
                    notify.status = NotificationStatus.SENDING_FORBIDDEN
                    sending_forbidden.append(notify)
                    continue

            is_allowed, next_send_time = self._is_in_allowed_time_range(
                notify, start_hour, end_hour
            )
            if is_allowed:
                send_now.append(notify)
            else:
                notify.target_sent_at = next_send_time  # type: ignore
                notify.status = NotificationStatus.DELAYED
                send_later.append(notify)
                logger.debug(f"Уведомление {notify.id} отложено до {next_send_time}")

        logger.info(
            f"Уведомлений для отправки сейчас: {len(send_now)}, "
            f"для отложенной отправки: {len(send_later)}"
        )
        return send_now, send_later, sending_forbidden

    def _is_in_allowed_time_range(  # noqa: WPS210
        self, notify: Notification, start_hour: int, end_hour: int
    ) -> tuple[bool, datetime | None]:
        """
        Проверяет, находится ли текущее время в таймзоне пользователя в разрешенном диапазоне.
        Возвращает кортеж: (можно ли отправить сейчас, время следующей отправки)
        """
        try:
            utc_now = datetime.now(ZoneInfo("UTC"))
            user_timezone = notify.user_timezone
            if not user_timezone:
                logger.warning(f"Таймзона не указана для уведомления {notify.id}, отправляем")
                return True, None

            # Преобразуем UTC время в время пользователя
            user_time = utc_now.astimezone(ZoneInfo(user_timezone))
            current_hour = user_time.hour

            is_allowed = start_hour <= current_hour < end_hour

            logger.debug(
                f"Уведомление {notify.id}: текущее время"
                f"пользователя {user_time.strftime('%H:%M')} "
                f"({user_timezone}), разрешено: {is_allowed}"
            )

            if is_allowed:
                return True, None
            else:
                next_send_time = self._calculate_next_send_time(user_time, start_hour, end_hour)
                # Конвертируем время отправки обратно в UTC для хранения
                next_send_time_utc = next_send_time.astimezone(ZoneInfo("UTC"))
                return False, next_send_time_utc

        except Exception as e:
            logger.error(f"Ошибка при проверке времени для уведомления {notify.id}: {e}")
            return True, None

    def _calculate_next_send_time(
        self, user_time: datetime, start_hour: int, end_hour: int
    ) -> datetime:
        """
        Вычисляет время следующей отправки уведомления в таймзоне пользователя.
        """
        # Создаем время начала отправки на сегодня
        today_start = user_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)

        # Если сейчас еще рано (до start_hour), отправляем сегодня в start_hour
        if user_time.hour < start_hour:
            return today_start

        # Если сейчас уже поздно (после end_hour), отправляем завтра в start_hour
        tomorrow_start = today_start + timedelta(days=1)
        return tomorrow_start


def get_priority_manager() -> PriorityManager:
    return PriorityManager()
