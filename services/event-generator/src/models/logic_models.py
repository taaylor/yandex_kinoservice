from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class FilmsType(StrEnum):
    FREE = "FREE"
    PAID = "PAID"
    ARCHIVED = "ARCHIVED"


class FilmListSchema(BaseModel):
    """Схема, представляющая сокращенную информацию о фильмах."""

    uuid: UUID = Field(..., description="Уникальный идентификатор фильма.")
    title: str = Field(
        ...,
        description="Название фильма.",
    )
    imdb_rating: float | None = Field(
        None,
        description="Рейтинг фильма по версии IMDB. Может отсутствовать.",
    )
    type: FilmsType = Field(..., description="Тип фильма")


class FilmListSchemaRequest(BaseModel):
    film_id: str = Field(..., description="Уникальный идентификатор фильма.")
