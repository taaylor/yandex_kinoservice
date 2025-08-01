import logging
from typing import Any
from uuid import UUID

import backoff
import httpx
from core.config import app_config
from models.logic_models import FilmResponse
from pydantic import TypeAdapter
from suppliers.base_supplier import BaseSupplier
from utils.http_decorators import EmptyServerResponse, handle_http_errors

logger = logging.getLogger(__name__)


class FilmSupplier(BaseSupplier):

    async def fetch_films(self, films: list[UUID]) -> list[FilmResponse]:
        """Получает список фильмов, соответствующих заданному вектору эмбеддинга."""
        url = app_config.filmapi.get_film_url
        data = {"film_ids": [str(f) for f in films]}

        films_json = await self._make_request(url, data)
        list_films = self._convert_to_model(films_json, FilmResponse)

        return list_films

    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, httpx.HTTPStatusError),
        max_tries=3,
        jitter=backoff.full_jitter,
    )
    @handle_http_errors(service_name=app_config.filmapi.host)
    async def _make_request(
        self, url: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Выполняет HTTP-запрос к внешнему API."""
        async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as client:

            logger.debug(f"Сформирована строка запроса: {url}")

            response = await client.post(url=url, json=data)
            response.raise_for_status()

            if not response.content:
                logger.error(f"Пустой ответ от сервиса {app_config.filmapi.host}")
                raise EmptyServerResponse("Получен пустой ответ от сервиса фильмов")

            response_data = response.json()

            logger.debug(
                f"Получен ответ от сервиса {app_config.filmapi.host}: "
                f"{len(response_data)} фильмов"
            )
            return response_data

    def _convert_to_model(
        self, json: list[dict[str, Any]], model: type[FilmResponse]
    ) -> list[FilmResponse]:
        """Преобразует JSON-ответ в список объектов модели."""

        adapter = TypeAdapter(list[FilmResponse])
        return adapter.validate_python(json)


def get_film_supplier() -> FilmSupplier:
    """Возвращает экземпляр поставщика фильмов."""
    return FilmSupplier()
