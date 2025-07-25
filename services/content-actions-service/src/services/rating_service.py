import asyncio
import json
import logging
from functools import lru_cache
from uuid import UUID

from api.v1.rating.schemas import AvgRatingResponse, ScoreResponse
from core.config import app_config
from db.cache import Cache, get_cache
from fastapi import Depends
from services.rating_repository import RatingRepository, get_rating_repository
from utils.aiokafka_conn import AIOMessageBroker, get_broker_connector

logger = logging.getLogger(__name__)

CACHE_KEY_AVG_RATING = "films:avg_rating:"


class RatingService:
    """Сервис для работы с рейтингом фильмов."""

    __slots__ = ("cache", "repository", "message_broker")

    def __init__(
        self, cache: Cache, repository: RatingRepository, message_broker: AIOMessageBroker
    ):
        """
        Инициализирует сервис с кешем и репозиторием.

        :param cache: Экземпляр Cache для кеширования результатов.
        :param repository: Репозиторий RatingRepository для работы с БД.
        """
        self.cache = cache
        self.repository = repository
        self.message_broker = message_broker

    async def get_average_rating(
        self, film_id: UUID, user_id: UUID | None
    ) -> AvgRatingResponse | None:
        """
        Возвращает рейтинг фильма

        :param film_id: UUID фильма, для которого нужно получить средний рейтинг.
        :return: Экземпляр AvgRatingResponse с полями:
                 - film_id: UUID фильма
                 - avg_rating: среднее арифметическое оценок (float)
                 - votes_count: количество голосов (int);
                 или None, если для фильма нет оценок.
        """
        str_film_id = str(film_id)
        cache_key = CACHE_KEY_AVG_RATING + str_film_id
        avg_rating_cache = await self.cache.get(cache_key)
        user_score = await self.get_user_score(
            user_id=user_id,
            film_id=film_id,
        )
        if avg_rating_cache:
            logger.debug(f"Рейтинг фильма {str_film_id} получен из кеша по ключу: {cache_key}")
            return AvgRatingResponse(
                **json.loads(avg_rating_cache),
                user_score=int(user_score) if user_score is not None else None,  # noqa: WPS504
            )

        avg_rating = await self.repository.calculate_average_rating(
            self.repository.collection.film_id == film_id
        )

        if not avg_rating:
            return None

        await self.cache.background_set(
            key=cache_key,
            value=avg_rating[0].model_dump_json(),
            expire=app_config.cache_expire_in_seconds,
        )

        logger.debug(f"Рейтинг фильма {str_film_id} будет сохранён в кеш по ключу {cache_key}.")
        return AvgRatingResponse(
            **avg_rating[0].model_dump(),
            user_score=int(user_score) if user_score is not None else None,  # noqa: WPS504
        )

    async def get_user_score(  # noqa: WPS615
        self,
        user_id: UUID | None,
        film_id: UUID,
    ) -> float | None:
        """
        Сохраняет/обновляет оценку фильма поставленную авторизованным пользователем.

        :param user_id: UUID пользователя, ставящего оценку.
        :param film_id: UUID фильма, для которого ставится оценка.
        """
        document = await self.repository.get_document(
            self.repository.collection.user_id == user_id,
            self.repository.collection.film_id == film_id,
        )
        if document:
            return document.score
        return None

    async def set_user_score(  # noqa: WPS615
        self, user_id: UUID, film_id: UUID, score: int
    ) -> ScoreResponse:
        """
        Сохраняет/обновляет оценку фильма поставленную авторизованным пользователем.

        :param user_id: UUID пользователя, ставящего оценку.
        :param film_id: UUID фильма, для которого ставится оценка.
        :param score: Оценка пользователя (int, строго 1–10).
        :return: Экземпляр ScoreResponse с полями:
                 - user_id: UUID пользователя
                 - film_id: UUID фильма
                 - created_at: время создания/вставки документа
                 - updated_at: время последнего обновления
                 - score: значение оценки
        """

        cache_key = CACHE_KEY_AVG_RATING + str(film_id)
        document = await self.repository.upsert(
            self.repository.collection.user_id == user_id,
            self.repository.collection.film_id == film_id,
            user_id=user_id,
            film_id=film_id,
            score=score,
        )
        result = ScoreResponse(
            user_id=document.user_id,
            film_id=document.film_id,
            created_at=document.created_at,
            updated_at=document.updated_at,
            score=document.score,
        )
        asyncio.create_task(
            self.message_broker.push_message(
                topic=app_config.kafka.rec_user_ratings_films_topic, value=result.model_dump_json()
            )
        )
        logger.debug(
            f"Пользователь - {str(user_id)}\n,"
            f" оценил фильм {str(film_id)}\n."
            f" Оценка: {score}."
        )
        avg_rating = await self.repository.calculate_average_rating(
            self.repository.collection.film_id == film_id
        )
        if avg_rating:
            await self.cache.background_set(
                key=cache_key,
                value=avg_rating[0].model_dump_json(),
                expire=app_config.cache_expire_in_seconds,
            )
            logger.debug(
                f"Рейтинг фильма {str(film_id)} будет сохранён в кеш по ключу {cache_key}."
            )
        return result

    async def delete_user_score(self, user_id: UUID, film_id: UUID) -> None:
        """
        Удаляет оценку фильма поставленную авторизованным пользователем.

        :param user_id: UUID пользователя.
        :param film_id: UUID фильма.
        :return: None.
        """

        cache_key = CACHE_KEY_AVG_RATING + str(film_id)
        deleted = await self.repository.delete_document(
            self.repository.collection.user_id == user_id,
            self.repository.collection.film_id == film_id,
        )
        logger.debug(
            f"Пользователь - {str(user_id)}\n," f" отозвал оценку фильма {str(film_id)}\n."
        )
        if deleted:
            avg_rating = await self.repository.calculate_average_rating(
                self.repository.collection.film_id == film_id
            )
            if avg_rating:
                await self.cache.background_set(
                    key=cache_key,
                    value=avg_rating[0].model_dump_json(),
                    expire=app_config.cache_expire_in_seconds,
                )
                logger.debug(
                    f"Рейтинг фильма {str(film_id)} будет сохранён в кеш по ключу {cache_key}."
                )


@lru_cache()
def get_rating_service(
    cache: Cache = Depends(get_cache),
    repository: RatingRepository = Depends(get_rating_repository),
    message_broker: AIOMessageBroker = Depends(get_broker_connector),
) -> RatingService:
    return RatingService(cache, repository, message_broker)
