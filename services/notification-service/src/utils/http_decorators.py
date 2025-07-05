"""
Декораторы для обработки ошибок HTTP запросов к внешним сервисам
"""

import logging
from functools import wraps
from typing import Any, Callable

import httpx
from pydantic import ValidationError as PydanticValidationError

logger = logging.getLogger(__name__)


class ExternalServiceError(Exception):
    """Базовое исключение для внешних сервисов"""


class ServiceUnavailableError(ExternalServiceError):
    """Внешний сервис недоступен"""


class DataValidationError(ExternalServiceError):
    """Ошибка валидации данных от внешнего сервиса"""


class EmptyServerResponse(ExternalServiceError):
    """Получен пустой ответ"""


def handle_http_errors(service_name: str = "внешний сервис") -> Callable:  # noqa: WPS238, WPS231
    """
    Декоратор для обработки HTTP ошибок при запросам к внешним сервисам

    Args:
        service_name: Название сервиса для логирования
        user_id_param: Название параметра с user_id для извлечения из аргументов
    """

    def decorator(func: Callable) -> Callable:  # noqa: WPS238, WPS231
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:  # noqa: WPS238, WPS231, WPS225
            try:  # noqa: WPS225
                return await func(*args, **kwargs)
            except httpx.TimeoutException:
                logger.error(f"Таймаут при запросе к {service_name}")
                raise ServiceUnavailableError(f"Таймаут при запросе к {service_name}")
            except httpx.ConnectError:
                logger.error(f"Ошибка подключения к {service_name}")
                raise ServiceUnavailableError(f"Ошибка подключения к {service_name}")
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP ошибка {e.response.status_code} при запросе к {service_name}")
                raise ServiceUnavailableError(
                    f"HTTP ошибка {e.response.status_code} при запросе к {service_name}"
                )
            except httpx.InvalidURL:
                logger.error(f"Некорректный URL для {service_name}")
                raise DataValidationError(f"Некорректный URL для {service_name}")
            except PydanticValidationError as e:
                logger.error(f"Ошибка валидации данных от {service_name}")
                raise DataValidationError(f"Некорректная структура данных от {service_name}: {e}")
            except EmptyServerResponse as e:
                logger.error(f"Получен пустой объект вместо данных от {service_name}")
                raise EmptyServerResponse(
                    f"Получен пустой объект вместо данных от {service_name}: {e}"
                )
            except Exception as e:
                logger.error(f"Неожиданная ошибка при запросе к {service_name}")
                raise ServiceUnavailableError(
                    f"Неожиданная ошибка при запросе к {service_name}: {e}"
                )

        return wrapper

    return decorator
