import logging
from typing import Annotated

from fastapi import APIRouter, Body, status
from models.logic_models import FilmListSchema

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    path="/get-films",
    status_code=status.HTTP_200_OK,
)
async def get_films(
    request_body: Annotated[
        list[FilmListSchema], Body(description="Данные пришедшие от event-generator")
    ],
):
    return request_body
