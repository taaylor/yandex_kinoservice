import logging

import backoff
import httpx
from core.config import app_config
from models.logic_models import LlmResponse
from pydantic import ValidationError
from suppliers.base_supplier import BaseSupplier
from utils.http_decorators import EmptyServerResponse, handle_http_errors

logger = logging.getLogger(__name__)


class LlmSupplier(BaseSupplier):

    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, httpx.HTTPStatusError),
        max_tries=3,
        jitter=backoff.full_jitter,
    )
    @handle_http_errors(service_name=app_config.filmapi.host)
    async def execute_nlp(self, genres: set[str], query: str) -> LlmResponse:  # noqa: WPS210
        """Выполняет запрос к LLM для обработки пользовательского запроса."""

        async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as client:

            prompt = app_config.llm.prompt.format(genres=genres, query=query)

            data = {
                "model": app_config.llm.model,
                "prompt": prompt,
                "stream": False,
                "format": app_config.llm.resp_format,
            }
            headers = {"Content-Type": "application/json"}
            url = app_config.llm.get_url

            logger.debug(f"Сформирована строка запроса: {url}")
            logger.debug(f"Сформирована data запроса: {data}")

            response = await client.post(url=url, json=data, headers=headers)
            response.raise_for_status()
            if not response.content:
                logger.error(f"Пустой ответ от сервиса {app_config.llm.host}")
                raise EmptyServerResponse("Получен пустой ответ от llm")

            try:
                response_data = response.json()
                logger.debug(f"Получен ответ от сервиса {app_config.llm.host}: {response_data}")

                nlp_result = LlmResponse.model_validate_json(response_data["response"])
                return nlp_result
            except ValidationError as e:
                logger.error(f"LLM Ответила с некорректным форматом: {e}")
                return LlmResponse(
                    status="Ошибка при обработке запроса. Пожалуйста, попробуйте ещё раз."
                )


def get_llm_supplier() -> LlmSupplier:
    """Возвращает экземпляр поставщика LLM."""
    return LlmSupplier(app_config.llm.timeout)
