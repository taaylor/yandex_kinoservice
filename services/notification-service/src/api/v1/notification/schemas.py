from uuid import UUID

from pydantic import BaseModel, Field


class ModelResponse(BaseModel):
    """Пример базовой модели ответа"""


class MockSchemaRequest(BaseModel):
    film_id: UUID = Field(
        ...,
        description="Уникальный идентификатор фильма.",
    )
