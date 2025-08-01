from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from models.enums import EventType, NotificationMethod, Priority
from pydantic import BaseModel, Field


class SingleNotificationRequest(BaseModel):
    """Запрос на создание одиночного уведомления"""

    user_id: UUID = Field(
        ..., description="Уникальный идентификатор пользователя, которому предназначено уведомление"
    )
    event_type: EventType = Field(
        EventType.TEST,
        description="Тип уведомления (действие/ситуация, которые привели к отправке уведомления)",
    )
    source: str = Field(..., description="Сервис запрашивающий уведомление")
    method: NotificationMethod = Field(..., description="Канал для уведомления пользователя")
    priority: Priority = Field(
        Priority.LOW,
        description="Приоритет, с которым будет отправлено уведомление. HIGH доставляются без учёта таймзоны пользователя",  # noqa: E501
    )
    event_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Контекст события, которое привело к запросу на нотификацию",
    )
    target_sent_at: datetime | None = Field(
        datetime.now(timezone.utc), description="Желаемое время отправки уведомления"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "a88cbbeb-b998-4ca6-aeff-501463dcdaa0",
                    "event_type": "USER_REVIEW_LIKED",
                    "source": "content-api",
                    "method": "WEBSOCKET",
                    "priority": "HIGH",
                    "event_data": {
                        "liked_by_user_id": "cf3d6829-5f95-4e64-acf2-70a6e0f27909",
                        "review_id": "f59ac58a-64a5-41f3-bae4-f4a8aefab8b0",
                        "film_id": "3e5351d6-4e4a-486b-8529-977672177a07",
                    },
                }
            ]
        }
    }


class SingleNotificationResponse(BaseModel):
    """Ответ о создании одиночного уведомления"""

    notification_id: UUID = Field(
        ..., description="Уникальный идентификатор экземпляра уведомления"
    )


class UpdateSendingStatusRequest(BaseModel):
    sent_success: list[UUID] = Field(
        default_factory=list, description="Список успешно отправленных уведомлений"
    )
    failure: list[UUID] = Field(
        default_factory=list, description="Список уведомлений, которые не удалось отправить"
    )


class UpdateSendingStatusResponse(BaseModel):
    updated: list[UUID] = Field(default_factory=list, description="Список обновлённых уведомлений")


class MassNotificationRequest(BaseModel):
    """Запрос на создание массовой рассылки всем пользователям"""

    event_type: EventType = Field(
        EventType.AUTO_MASS_NOTIFY,
        description="Тип уведомления (действие/ситуация, которые привели к отправке уведомления)",
    )
    source: str = Field(..., description="Сервис запрашивающий уведомление")
    method: NotificationMethod = Field(..., description="Канал для уведомления пользователя")
    priority: Priority = Field(
        Priority.LOW,
        description="Приоритет, с которым будет отправлено уведомление. HIGH доставляются без учёта таймзоны пользователя",  # noqa: E501
    )
    event_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Контекст события, которое привело к запросу на нотификацию",
    )
    target_sent_at: datetime | None = Field(
        datetime.now(timezone.utc), description="Желаемое время отправки уведомления"
    )
    template_id: UUID | None = Field(
        default=None,
        description="Идентификатор шаблона, который будет использоваться для массовой рассылки",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "event_type": "AUTO_MASS_NOTIFY",
                    "source": "event-generator",
                    "method": "EMAIL",
                    "priority": "HIGH",
                    "template_id": "d3b2f1c4-5e6f-4c8b-9f3d-2e1f5a6b7c8d",
                    "event_data": {
                        "recommended_films": [
                            {
                                "film_id": "26ee1cee-741a-417f-ad75-2890d8f69e8e",
                                "film_title": "Горбатая гора",
                                "imdb_rating": 10,
                            },
                            {
                                "film_id": "8bd861d1-357e-4649-8799-6915090d90db",
                                "film_title": "Властелин колец",
                                "imdb_rating": 9.5,
                            },
                            {
                                "film_id": "3a573f34-6071-425a-91aa-97cb229c44cf",
                                "film_title": "Звёздные войны",
                                "imdb_rating": 8.7,
                            },
                        ]
                    },
                }
            ]
        }
    }


class MassNotificationResponse(BaseModel):
    """Ответ о создании массовой рассылки"""

    notification_id: UUID = Field(
        ..., description="Уникальный идентификатор экземпляра уведомления"
    )


# ! -=-=-=-=-=-=- схемы для моковой ручки принятия массовой рассылки -=-=-=-=-=-=-
class FilmListSchema(BaseModel):
    """Схема для ответа API, представляющая полную информацию о фильме."""

    film_id: UUID = Field(
        ...,
        description="Уникальный идентификатор фильма.",
    )
    film_title: str = Field(
        ...,
        description="Название фильма.",
    )
    imdb_rating: float | None = Field(
        None,
        description="Рейтинг фильма по версии IMDB.",
    )


class RecomendedFilmsSchema(BaseModel):
    recommended_films: list[FilmListSchema] = Field(
        default_factory=list,
        description="Список жанров фильма.",
    )


class RequestToMassNotificationSchema(BaseModel):
    target_start_sending_at: datetime = Field(
        ...,
        description="Начало запуска рассылки",
    )
    event_data: RecomendedFilmsSchema = Field(
        ...,
        description="Список рекомендуемых фильмов.",
    )
    template_id: UUID = Field(
        ...,
        description="UUID шаблона для email.",
    )
