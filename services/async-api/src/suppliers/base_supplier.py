import logging
from http import HTTPMethod
from typing import Any

import backoff
import httpx
from utils.http_decorators import handle_http_errors

logger = logging.getLogger(__name__)


class BaseSupplier:

    def __init__(self, timeout: int, service_name: str):
        self.timeout = timeout
        self.service_name = service_name

    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, httpx.HTTPStatusError),
        max_tries=3,
        jitter=backoff.full_jitter,
    )
    @handle_http_errors()
    async def _make_request(
        self, method: HTTPMethod, url: str, data: dict | None = None, params: dict | None = None
    ) -> dict[str, Any] | None:

        async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as client:
            logger.debug(f"Сформирована строка запроса: {url}")

            match method:
                case HTTPMethod.POST:
                    response = await client.post(url=url, json=data, params=params)
                    response.raise_for_status()
                case HTTPMethod.GET:
                    response = await client.get(url=url, params=params)
                    response.raise_for_status()
                case _:
                    raise ValueError(f"Метод: {method} не поддерживается.")

            if not response.content:
                logger.error(f"Пустой ответ от сервиса {self.service_name}")

            response_data = response.json()
            logger.debug(f"Получен ответ от сервиса {self.service_name}: {response_data}")
            return response_data
