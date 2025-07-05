from enum import StrEnum
from uuid import UUID

from models.schemas_logic import FilmLogic, GenreLogic, PersonLogic
from pydantic import BaseModel, Field


class FilmsType(StrEnum):
    FREE = "FREE"
    PAID = "PAID"
    ARCHIVED = "ARCHIVED"


class FilmsRequest(BaseModel):
    film_ids: list[UUID] = Field(
        ...,
        description="Список идентификаторов фильмов, которые нужно получить",
        min_length=1,
        max_length=1000,
    )


class FilmInternalResponse(BaseModel):
    """Схема для ответа API, представляющая полную информацию о фильме."""

    uuid: UUID = Field(
        ...,
        description="Уникальный идентификатор фильма.",
    )
    title: str = Field(
        ...,
        description="Название фильма.",
    )
    imdb_rating: float | None = Field(
        None,
        description="Рейтинг фильма по версии IMDB.",
    )
    description: str | None = Field(
        None,
        description="Описание фильма.",
    )
    genre: list[GenreLogic] = Field(
        default_factory=list,
        description="Список жанров фильма.",
    )
    actors: list[PersonLogic] = Field(
        default_factory=list,
        description="Список актеров фильма.",
    )
    writers: list[PersonLogic] = Field(
        default_factory=list,
        description="Список сценаристов фильма.",
    )
    directors: list[PersonLogic] = Field(
        default_factory=list,
        description="Список режиссеров фильма.",
    )
    type: FilmsType = Field(..., description="Тип фильма")

    @classmethod
    def transform_from_FilmLogic(cls, film: FilmLogic) -> "FilmInternalResponse":
        return cls(
            uuid=film.id,
            title=film.title,
            description=film.description,
            imdb_rating=film.imdb_rating,
            genre=film.genres,
            directors=film.directors,
            actors=film.actors,
            writers=film.writers,
            type=film.type,
        )
