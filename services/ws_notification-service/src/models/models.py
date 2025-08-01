from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Priority(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EventSchemaMessage(BaseModel):
    """Схема сообщения события для очереди."""

    id: str = Field(description="Уникальный идентификатор уведомления")
    user_id: str = Field(description="Идентификатор пользователя, которому адресовано уведомление")
    method: str = Field(
        description="Метод доставки уведомления (например, WEBSOCKET)", exclude=True
    )
    source: str = Field(description="Источник уведомления (например, content-api)", exclude=True)
    status: str = Field(description="Статус уведомления (например, sent, failed)", exclude=True)
    target_sent_at: str = Field(description="Время отправки уведомления пользователю", exclude=True)
    actual_sent_at: str | None = Field(
        default=None, description="Фактическое время отправки уведомления", exclude=True
    )
    added_queue_at: str | None = Field(
        default=None, description="Время добавления уведомления в очередь", exclude=True
    )
    priority: Priority = Field(description="Приоритет уведомления (например, LOW)")
    event_type: str = Field(description="Тип уведомления (например, user_review_liked)")
    event_data: dict[str, Any] = Field(default_factory=dict, description="Данные уведомления")
    user_timezone: str | None = Field(
        default=None, description="Часовой пояс пользователя", exclude=True
    )
    template_id: str | None = Field(
        default=None, description="Идентификатор шаблона уведомления", exclude=True
    )
    mass_notification_id: str | None = Field(
        default=None, description="Идентификатор массового уведомления", exclude=True
    )


class EventsIdsLogic(BaseModel):
    """Схема для хранения статусов отправленных событий."""

    sent_success: list[str] = Field(
        default_factory=list, description="Список успешно отправленных уведомлений"
    )
    failure: list[str] = Field(
        default_factory=list, description="Список уведомлений, которые не удалось отправить"
    )
