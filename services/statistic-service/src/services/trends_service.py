import logging
from functools import lru_cache
from typing import Annotated

from api.v1.schemas import DayEnum, PeriodEnum, TrendFilm, TrendsFilmsResponse
from core.config import app_config
from db.abstract import DBAbstract
from db.clickhouse import get_chclient
from fastapi import Depends

logger = logging.getLogger(__name__)


class TrendsService:

    __slots__ = ("client",)

    def __init__(self, client: DBAbstract):
        self.client = client

    async def fetch_trends_films(self, page_size: int, period: PeriodEnum) -> TrendsFilmsResponse:
        logger.debug(
            "Поступил запрос на получение трендовых "
            f"фильмов с параметрами {page_size=}, {period=}"
        )

        match period:
            case PeriodEnum.WEEKLY:
                day = DayEnum.WEEKLY.value
            case PeriodEnum.MONTHLY:
                day = DayEnum.MONTHLY.value
            case _:
                logger.warning(f"Получен период, который не ожидался {period=}")
                day = DayEnum.DEFAULT.value

        trends_films_db = await self.client.fetch(
            """
            SELECT
                film_uuid,
                sumMerge(total_score) AS total_score
            FROM {db}.{table}
            WHERE event_date >= (NOW() - INTERVAL {period} DAY)
            GROUP BY film_uuid
            ORDER BY total_score DESC
            LIMIT {page_size}
            """.format(
                page_size=page_size,
                period=day,
                db=app_config.clickhouse.database,
                table=app_config.clickhouse.table_trends_aggr_data_dist,
            )
        )
        trends_films = []
        if trends_films_db:
            logger.info(f"Получено {len(trends_films_db)} трендовых фильмов по периоду {period=}")
            trends_films = [
                TrendFilm(film_uuid=record.get("film_uuid"), total_score=record.get("total_score"))
                for record in trends_films_db
            ]
        return TrendsFilmsResponse(period=period, trends_films=trends_films)


@lru_cache
def get_trends_service(client: Annotated[DBAbstract, Depends(get_chclient)]) -> TrendsService:
    return TrendsService(client=client)
