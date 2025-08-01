import logging
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from api.v1.nlp.schemas import Film, RecsRequest, RecsResponse
from db.postgres import get_session
from fastapi import Depends
from models.enums import ProcessingStatus
from models.logic_models import FilmListResponse
from models.models import ProcessedNpl
from services.base_service import BaseService
from services.repository.nlp_repository import NlpRepository, get_nlp_repository
from sqlalchemy.ext.asyncio import AsyncSession
from suppliers.embedding_supplier import EmbeddingSupplier, get_embedding_supplier
from suppliers.film_supplier import FilmSupplier, get_film_supplier
from suppliers.llm_supplier import LlmSupplier, get_llm_supplier

logger = logging.getLogger(__name__)


class NlpService(BaseService):
    def __init__(
        self,
        repository: NlpRepository,
        session: AsyncSession,
        llm_client: LlmSupplier,
        film_supplier: FilmSupplier,
        embedding_supplier: EmbeddingSupplier,
    ) -> None:
        super().__init__(repository, session)
        self.llm_client = llm_client
        self.film_supplier = film_supplier
        self.embedding_supplier = embedding_supplier

    async def process_nl_query(  # noqa: WPS210
        self, user_id: UUID, request_body: RecsRequest
    ) -> RecsResponse:
        """Метод обрабатывает запрос пользователя на натуральном
        языке и отдаёт фильмы или запрос на уточнение."""
        embedding = []
        films = None
        genres = await self.film_supplier.fetch_genres()
        logger.debug(f"Получен список жанров: {genres}")

        llm_resp = await self.llm_client.execute_nlp(genres, request_body.query)

        if llm_resp.status == ProcessingStatus.OK:
            llm_resp_status = ProcessingStatus.OK
            embedding = await self._fetch_embedding(request_body.query)
            raw_films = await self._fetch_films(embedding)
            films = [Film.model_validate(film.model_dump(mode="python")) for film in raw_films]
            message = "Отличный выбор!"
        else:
            llm_resp_status = ProcessingStatus.INCORRECT_QUERY
            message = llm_resp.status

        processed_nlp = ProcessedNpl(
            user_id=user_id,
            query=request_body.query,
            processing_result=llm_resp_status,
            llm_resp=llm_resp.model_dump(mode="json"),
            final_embedding=embedding,
        )
        await self._write_result_to_repository(processed_nlp)

        response = RecsResponse(films=films, message=message)
        logger.info(
            f"Пользователь получил рекомендации для запроса: {request_body.query}. "
            f"Рекомендуемые фильмы: {response.model_dump_json(indent=4)}"
        )
        return response

    async def _fetch_films(self, embedding: list[float]) -> list[FilmListResponse]:
        """Получает список фильмов на основе эмбеддинга."""
        films = await self.film_supplier.fetch_films(embedding)

        logger.info(
            f"Для запроса пользователя получен список фильмов: {films[:2]}, "
            f"количество {len(films)}"
        )
        return films

    async def _fetch_embedding(self, query: str) -> list[float]:
        """Генерирует эмбеддинг для пользовательского запроса."""
        query_embedding = await self.embedding_supplier.fetch_embedding(query)

        logger.info(
            f"Для запроса пользователя получен эмбеддинг: {query_embedding[:10]}, "
            f"размерность {len(query_embedding)}"
        )
        return query_embedding

    async def _write_result_to_repository(self, processing_result: ProcessedNpl) -> None:
        """Сохраняет результат обработки запроса в базу данных."""
        await self.repository.create_entity(self.session, processing_result)
        logger.info(
            f"В БД записан результат обработки пользовательского запроса {processing_result.id}"
        )


@lru_cache()
def get_nlp_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    repository: Annotated[NlpRepository, Depends(get_nlp_repository)],
    llm_client: Annotated[LlmSupplier, Depends(get_llm_supplier)],
    film_supplier: Annotated[FilmSupplier, Depends(get_film_supplier)],
    embedding_supplier: Annotated[EmbeddingSupplier, Depends(get_embedding_supplier)],
) -> NlpService:
    return NlpService(repository, session, llm_client, film_supplier, embedding_supplier)
