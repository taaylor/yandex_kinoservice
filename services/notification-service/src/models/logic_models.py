from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class UserProfile(BaseModel):
    user_id: UUID
    username: str
    first_name: str
    last_name: str
    gender: str
    role: str
    email: str
    is_fictional_email: bool
    is_email_notify_allowed: bool
    is_verified_email: bool
    user_timezone: str
    created_at: datetime


class Film(BaseModel):
    uuid: UUID
    title: str
    imdb_rating: float | None
    description: str | None
    genre: list[dict[str, Any]]
    actors: list[dict[str, Any]]
    writers: list[dict[str, Any]]
    directors: list[dict[str, Any]]
    type: str


class NotificationLogic(BaseModel):
    id: UUID
    user_id: UUID
    method: str
    source: str
    status: str
    target_sent_at: datetime
    actual_sent_at: datetime | None
    added_queue_at: datetime | None
    priority: str
    event_type: str
    event_data: dict[str, Any]
    user_timezone: str | None
    template_id: UUID | None
    mass_notification_id: UUID | None

    model_config = {"from_attributes": True}  # Включаем поддержку атрибутов ORM


class ProfilePaginate(BaseModel):
    profiles: list[UserProfile]
    page_current: int
    page_size: int
    page_total: int
