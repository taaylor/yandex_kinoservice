from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TimeFields(BaseModel):
    created_at: datetime
    updated_at: datetime


class FilmIdFiled(BaseModel):
    film_id: UUID


class UserFiled(BaseModel):
    user_id: UUID


class BookMarkEvent(TimeFields, FilmIdFiled, UserFiled):
    status: str
    comment: str | None


class RatingEvent(TimeFields, FilmIdFiled, UserFiled):
    score: int


class GenreLogic(BaseModel):
    id: UUID
    name: str


class QueryModel(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    text: str


class FilmResponse(BaseModel):
    uuid: UUID
    title: str
    imdb_rating: float | None
    description: str | None
    genre: list[GenreLogic]
    type: str
