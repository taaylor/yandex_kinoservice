import logging
from typing import Annotated

from api.v1.notification.schemas import MockSchemaRequest
from fastapi import APIRouter, Body, status

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(path="")
async def test() -> str:
    return "Succsess"


@router.post(
    path="/mock-get-films",
    status_code=status.HTTP_200_OK,
)
async def mock_get_films(
    request_body: Annotated[
        list[MockSchemaRequest], Body(description="Данные пришедшие от event-generator")
    ],
):
    return [{"id-from-notify": film.model_dump()["film_id"]} for film in request_body]
