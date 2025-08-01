import logging
from functools import lru_cache
from uuid import UUID

from core.config import app_config
from db.postgres import get_session_context
from models.enums import RecsSourceType
from models.logic_models import BookMarkEvent, FilmResponse, QueryModel, RatingEvent
from models.models import UserRecs
from services.base_service import BaseService
from services.repository.recs_repository import RecsRepository, get_recs_repository
from sqlalchemy.ext.asyncio import AsyncSession
from suppliers.embedding_supplier import EmbeddingSupplier, get_embedding_supplier
from suppliers.film_supplier import FilmSupplier, get_film_supplier

logger = logging.getLogger(__name__)


class RecsEventProcessor(BaseService[RecsRepository]):  # noqa: WPS214
    """Класс обрабатывает события из Kafka и сохраняет рекомендации в БД."""

    def __init__(
        self,
        repository: RecsRepository,
        session: AsyncSession,
        film_supplier: FilmSupplier,
        embedding_supplier: EmbeddingSupplier,
    ) -> None:
        super().__init__(repository, session)
        self.film_supplier = film_supplier
        self.embedding_supplier = embedding_supplier

    async def event_handler(self, topic: str, message: bytes) -> None:
        """Обрабатывает событие из Kafka в зависимости от его типа."""
        event = self._decode_message(topic, message)
        match event:
            case RatingEvent():
                await self._process_rating_event(event)
            case BookMarkEvent():
                await self._process_bookmark_event(event)

    def _decode_message(self, topic: str, message: bytes) -> RatingEvent | BookMarkEvent:
        """Декодирует сообщение из Kafka в объект события."""
        match topic:
            case app_config.kafka.rec_bookmarks_list_topic:
                decoded_message = message.decode("utf-8")
                logger.info(f"Получено сообщение из топика: {topic}: payload: {decoded_message}")
                return BookMarkEvent.model_validate_json(decoded_message)
            case app_config.kafka.rec_user_ratings_films_topic:
                decoded_message = message.decode("utf-8")
                logger.info(f"Получено сообщение из топика: {topic}: payload: {decoded_message}")
                return RatingEvent.model_validate_json(decoded_message)
            case _:
                logger.error(f"Невозможно обработать событие из топика {topic}")
                raise ValueError(f"Сообщение из неизвестного топика {topic}")

    async def _process_bookmark_event(self, event: BookMarkEvent):
        """Обрабатывает событие создания закладки."""
        logger.debug(f"Обрабатываю событие создания закладки: {event.model_dump_json(indent=4)}")

        embedding = await self._fetch_embedding(event.film_id)
        await self._save_rec_to_repository(event, RecsSourceType.ADD_BOOKMARKS, embedding)

    async def _process_rating_event(self, event: RatingEvent):
        """Обрабатывает событие оценки фильма."""
        logger.debug(f"Обрабатываю событие оценки фильма: {event.model_dump_json(indent=4)}")

        if event.score < app_config.high_rating_score:
            logger.info(
                f"Пользователь недостаточно высоко оценил фильм для создания рекомендации: {event.score}"  # noqa: E501
            )

        embedding = await self._fetch_embedding(event.film_id)
        await self._save_rec_to_repository(event, RecsSourceType.HIGH_RATING, embedding)

    async def _fetch_embedding(self, film_id: UUID) -> list[float]:
        """Получает эмбеддинг для фильма по его идентификатору."""
        # TODO: Можно переделывать на получение всех фильмов и эмбеддингов пакетом при чтении батча.
        film_description = await self._fetch_film_description(film_id)
        embedding_query = QueryModel(id=film_id, text=film_description)
        embedding = await self.embedding_supplier.fetch_embedding([embedding_query])
        logger.debug(f"Создан эмбеддинг для фильма: {film_id}, {embedding[film_id][:10]}")
        return embedding[film_id]

    async def _fetch_film_description(self, film_id: UUID) -> str:
        """Получает описание фильма по его идентификатору."""
        films = await self.film_supplier.fetch_films([film_id])
        logger.info(
            f"Для создания рекомендации получен фильм: {films[0].model_dump_json(indent=4)}"
        )
        embedding_text = self._build_embedding_text(films[0])
        logger.debug(f"Для фильма сгенерирован текст будущего эмбеддинга: {embedding_text}")
        return embedding_text

    def _build_embedding_text(
        self,
        film: FilmResponse,
    ) -> str:
        """Создает текст для эмбеддинга на основе данных фильма."""
        return app_config.template_film_embedding.format(
            title=film.title,
            genres=", ".join([genre.name for genre in film.genre]),
            description=film.description,
            rating_text=film.imdb_rating,
        )

    async def _save_rec_to_repository(
        self,
        event: BookMarkEvent | RatingEvent,
        source_type: RecsSourceType,
        embedding: list[float],
    ):
        """Сохраняет рекомендацию в репозиторий."""
        rec = UserRecs(
            user_id=event.user_id,
            film_id=event.film_id,
            rec_source_type=source_type,
            embedding=embedding,
        )
        async with self.session as session:
            await self.repository.add_now_rec(session, rec)


@lru_cache
def create_recs_event_processor() -> RecsEventProcessor:
    """Создает экземпляр процессора событий рекомендаций."""
    session = get_session_context()
    repository = get_recs_repository()
    film_supplier = get_film_supplier()
    embedding_supplier = get_embedding_supplier()

    return RecsEventProcessor(
        repository=repository,
        session=session,
        film_supplier=film_supplier,
        embedding_supplier=embedding_supplier,
    )
