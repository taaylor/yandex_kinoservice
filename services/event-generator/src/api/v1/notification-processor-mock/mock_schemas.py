from uuid import UUID

from pydantic import BaseModel


class GetFilmRequestBody(BaseModel):
    uuid_film = UUID
