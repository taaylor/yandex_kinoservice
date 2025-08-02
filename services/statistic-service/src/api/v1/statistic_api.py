from typing import Annotated

from api.v1.schemas import PeriodEnum, TrendsFilmsResponse
from fastapi import APIRouter, Depends, Query
from services.trends_service import TrendsService, get_trends_service

router = APIRouter()


@router.get(
    path="/fetch-trends-films",
    summary="Позволяет получить трендовые фильмы по фильтрам",
    description="Возвращает трендовые фильмы по переданной фильтрации",
    response_model=TrendsFilmsResponse,
)
async def fetch_trends_films(
    trends_service: Annotated[TrendsService, Depends(get_trends_service)],
    page_size: Annotated[
        int,
        Query(description="Количество трендовых фильмов, которых необходимо вернуть", ge=10, le=50),
    ] = 10,
    period: Annotated[PeriodEnum, Query(description="Период тренда")] = PeriodEnum.WEEKLY,
) -> TrendsFilmsResponse:
    return await trends_service.fetch_trends_films(page_size=page_size, period=period)
