from typing import Annotated

from api.v1.internal.schemas import FilmInternalResponse, FilmsRequest
from fastapi import APIRouter, Body, Depends
from services.filmwork import FilmService, get_film_service

router = APIRouter()


@router.post(
    "/fetch-films",
    response_model=list[FilmInternalResponse],
    summary="Получить подробную информацию о кинопроизведении",
    description=(
        "Возвращает полную информацию о кинопроизведении по его уникальному "
        "идентификатору (UUID). "
        "В ответ включены название, рейтинг, описание, жанры, актерский состав, \
        сценаристы и режиссеры."
    ),
    response_description="Подробная информация о кинопроизведении",
)
async def film_detail(
    film_service: Annotated[FilmService, Depends(get_film_service)],
    request_body: Annotated[FilmsRequest, Body(description="UUID кинопроизведений")],
) -> list[FilmInternalResponse]:
    """Endpoint для получения детальной информации о кинопроизведениях по UUID"""
    film_ids = request_body.film_ids
    films = await film_service.get_films_by_id_internal(
        film_ids=film_ids,
    )

    return films
