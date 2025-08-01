from typing import Annotated
from uuid import UUID

from api.v1.nlp.schemas import RecsRequest, RecsResponse
from auth_utils import get_current_user_id
from fastapi import APIRouter, Body, Depends
from services.nlp_service import NlpService, get_nlp_service

router = APIRouter()


@router.post(
    "/analyze",
    summary="Анализ пользовательского запроса и рекомендации фильмов",
    description="""Обрабатывает пользовательский запрос
                на русском языке и возвращает список рекомендуемых фильмов.
                Проверяет JWT-токен пользователя, извлекает идентификатор
                пользователя и передаёт запрос в сервис NLP для анализа.
                """,
    response_model=RecsResponse,
)
async def fetch_films_by_user_query(
    user_jwt_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[NlpService, Depends(get_nlp_service)],
    request_body: Annotated[RecsRequest, Body],
) -> RecsResponse:
    return await service.process_nl_query(user_jwt_id, request_body)
