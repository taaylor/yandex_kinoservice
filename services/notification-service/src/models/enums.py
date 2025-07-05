from enum import StrEnum


class EventType(StrEnum):
    TEST = "TEST"
    USER_REVIEW_LIKED = "USER_REVIEW_LIKED"
    USER_REGISTERED = "USER_REGISTERED"
    MASS_NOTIFY = "MASS_NOTIFY"


class Priority(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class NotificationMethod(StrEnum):
    EMAIL = "EMAIL"
    WEBSOCKET = "WEBSOCKET"


class NotificationStatus(StrEnum):
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    SENDING = "SENDING"
    SENT = "SENT"
    SENDING_FORBIDDEN = "SENDING_FORBIDDEN"
    DELAYED = "DELAYED"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    SENDING_ERROR = "SENDING_ERROR"


class MassNotificationStatus(StrEnum):
    NEW = "NEW"
    SENDING = "SENDING"
    SENT = "SENT"
    DELAYED = "DELAYED"
