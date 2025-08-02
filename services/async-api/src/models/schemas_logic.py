from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class FilmsType(StrEnum):
    FREE = "FREE"
    PAID = "PAID"
    ARCHIVED = "ARCHIVED"


class PeriodEnum(StrEnum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class PersonLogic(BaseModel):
    """Модель, для бизнес логики, представляющая человека (актера, сценариста, режиссера).

    Attributes:
        id (UUID): Уникальный идентификатор персоны.
        name (str): Имя персоны.

    """

    id: UUID
    name: str


class GenreLogic(BaseModel):
    """Схема для бизнес логики, представляющая информацию о жанре фильма.

    Attributes:
        id (UUID): Уникальный идентификатор жанра.
        name (str): Название жанра фильма.

    """

    id: UUID
    name: str


class FilmLogic(BaseModel):
    """Модель, для бизнес логики, представляющая информацию о фильме.

    Attributes:
        id (UUID): Уникальный идентификатор фильма.
        title (str): Название фильма.
        description (Optional[str]): Описание фильма (может отсутствовать).
        rating (Optional[float]): Рейтинг фильма (IMDB) (может отсутствовать).
        genres (list[str]): Список жанров фильма.
        directors (list[Person]): Список режиссеров фильма.
        actors (list[Person]): Список актеров, участвующих в фильме.
        writers (list[Person]): Список сценаристов фильма.
        actors_names (list[str]): Список имен актеров.
        writers_names (list[str]): Список имен сценаристов.
        directors_names (list[str]): Список имен режиссеров.

    """

    id: UUID
    title: str
    description: str | None = None
    imdb_rating: float | None = None
    genres: list[GenreLogic] = Field(default_factory=list)
    directors: list[PersonLogic] = Field(default_factory=list)
    actors: list[PersonLogic] = Field(default_factory=list)
    writers: list[PersonLogic] = Field(default_factory=list)
    actors_names: list[str] = Field(default_factory=list)
    writers_names: list[str] = Field(default_factory=list)
    directors_names: list[str] = Field(default_factory=list)
    type: FilmsType
