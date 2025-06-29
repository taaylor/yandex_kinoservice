from enum import StrEnum


class StatusesNotifi(StrEnum):
    """Перечисление статусов одиночного события"""

    NEW = "NEW"
    SENDING = "SENDING"
    SENT = "SENT"
    DELAYED = "DELAYED"
    SENDING_FORBIDDEN = "SENDING_FORBIDDEN"
    SENDING_ERROR = "SENDING_ERROR"


class GlobalStatusesNotifi(StrEnum):
    """Перечисление статусов глобального события"""

    NEW = "NEW"
    SENDING = "SENDING"
    SENT = "SENT"
    DELAYED = "DELAYED"
