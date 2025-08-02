import logging
from functools import lru_cache
from http import HTTPMethod
from typing import Any
from uuid import UUID

from core.config import app_config
from models.schemas_logic import PeriodEnum
from suppliers.base_supplier import BaseSupplier

logger = logging.getLogger(__name__)


class StatisticSupplier(BaseSupplier):

    async def fetch_trends_films(
        self, page_size: int = 10, period: PeriodEnum = PeriodEnum.WEEKLY
    ) -> list[UUID]:
        url = app_config.statistic_supplier.get_url
        params = {
            "page_size": page_size,
            "period": period.value,
        }
        trends_films = await self._make_request(
            method=HTTPMethod.GET,
            url=url,
            params=params,
        )
        return self._parsing_trends_films(trends_films)

    @staticmethod
    def _parsing_trends_films(trends_films: dict[str, Any]) -> list[UUID]:
        trends_films_dto = []
        if trends_films := trends_films.get("trends_films"):
            for film in trends_films:
                if film_id := film.get("film_uuid"):
                    trends_films_dto.append(UUID(film_id))
        return trends_films_dto


@lru_cache
def get_statistic_supplier() -> StatisticSupplier:
    return StatisticSupplier(
        service_name="statistic-service", timeout=app_config.statistic_supplier.timeout
    )
