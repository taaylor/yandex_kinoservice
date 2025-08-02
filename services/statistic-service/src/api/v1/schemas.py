from enum import IntEnum, StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class PeriodEnum(StrEnum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class DayEnum(IntEnum):
    DEFAULT = 1
    MONTHLY = 30
    WEEKLY = 7


class TrendFilm(BaseModel):
    film_uuid: UUID = Field(description="Идентификатор фильма")
    total_score: float = Field(description="Оценка фильма на основе метрик пользователя")


class TrendsFilmsResponse(BaseModel):
    period: PeriodEnum = Field(description="Период трендовых фильмов")
    trends_films: list[TrendFilm] = Field(
        description=("Список идентификаторов трендовых фильмов " "отсортированных по популярности"),
        default_factory=list,
    )
