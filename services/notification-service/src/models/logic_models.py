from datetime import datetime
from enum import StrEnum
from uuid import UUID

from models.enums import NotificationMethod, Priority
from pydantic import BaseModel


class GenderEnum(StrEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class UserProfile(BaseModel):
    user_id: UUID
    username: str
    first_name: str
    last_name: str
    gender: GenderEnum
    role: str
    email: str
    is_fictional_email: bool
    is_email_notify_allowed: bool
    is_verified_email: bool
    user_timezone: str
    created_at: datetime


class LikeNotification(BaseModel):
    id: UUID
    user_id: UUID
    source: str
    target_sent_at: datetime
    added_queue_at: datetime
    event_type: str
    updated_at: datetime
    method: NotificationMethod
    priority: Priority
    event_data: dict
    created_at: datetime
