import asyncio
import logging
from functools import lru_cache
from uuid import UUID

from api.v1.bookmark.schemas import (
    BookmarkObj,
    ChangeBookmarkRequest,
    ChangeBookmarkResponse,
    CreateBookmarkRequest,
    CreateBookmarkResponse,
    FetchBookmarkList,
)
from core.config import app_config
from db.cache import Cache, get_cache
from fastapi import Depends, HTTPException, status
from models.enum_models import FilmBookmarkState
from services.bookmark_repository import BookmarkRepository, get_bookmark_repository
from tracer_utils import traced
from utils.aiokafka_conn import AIOMessageBroker, get_broker_connector
from utils.film_id_validator import FilmIdValidator, get_film_id_validator

logger = logging.getLogger(__name__)

CACHE_KEY_USER_BOOKMARKS = "bookmarks:{user_id}:{page}"


class BookmarkService:
    """Класс реализую бизнес логику работы с списком просмотра фильмов"""

    __slots__ = ("cache", "repository", "film_id_validator", "message_broker")

    def __init__(self, cache, repository, film_id_validator, message_broker) -> None:
        self.cache: Cache = cache
        self.repository: BookmarkRepository = repository
        self.film_id_validator: FilmIdValidator = film_id_validator
        self.message_broker: AIOMessageBroker = message_broker

    @traced("add_now_bookmark_service_action")
    async def add_bookmark_by_film_id(
        self, user_id: UUID, film_id: UUID, request_body: CreateBookmarkRequest
    ) -> CreateBookmarkResponse:

        logger.info(f"Пользователь: {user_id=} добавляет фильм: {film_id=} в закладки")

        await self.film_id_validator.validate_film_id(film_id)

        inserted_bookmark = await self.repository.upsert(
            self.repository.collection.user_id == user_id,
            self.repository.collection.film_id == film_id,
            user_id=user_id,
            film_id=film_id,
            comment=request_body.comment,
            status=FilmBookmarkState.NOTWATCHED,
        )

        if inserted_bookmark:
            await self._invalidate_user_bookmark_cache(user_id)
            bookmark = CreateBookmarkResponse(
                film_id=inserted_bookmark.film_id,
                comment=inserted_bookmark.comment,
                status=inserted_bookmark.status,
                created_at=inserted_bookmark.created_at,
                updated_at=inserted_bookmark.updated_at,
            )
            asyncio.create_task(
                self.message_broker.push_message(
                    topic=app_config.kafka.rec_bookmarks_list_topic,
                    value=bookmark.model_dump_json(),
                )
            )
            return bookmark
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось добавить фильм в список просмотра",
        )

    async def remove_bookmark_by_film_id(self, user_id: UUID, film_id: UUID):
        await self.film_id_validator.validate_film_id(film_id)
        await self.repository.delete_document(
            self.repository.collection.user_id == user_id,
            self.repository.collection.film_id == film_id,
        )
        await self._invalidate_user_bookmark_cache(user_id=user_id)

    async def fetch_watchlist_by_user_id(
        self, user_id: UUID, page_size: int = 50, skip_page: int = 0
    ) -> FetchBookmarkList:

        logger.info(
            f"Пользователь: {user_id=} запрашивает список для просмотра с параметрами: {page_size=}, {skip_page=}"  # noqa: E501
        )

        user_cache_key = CACHE_KEY_USER_BOOKMARKS.format(user_id=user_id, page=skip_page + 1)
        cached_user_watchlist = await self.cache.get(key=user_cache_key)

        if cached_user_watchlist:
            logger.info(
                f"Список фильмов пользователя: {user_id=} для запроса: {page_size=}, {skip_page=} найден в кэше"  # noqa: E501
            )
            return FetchBookmarkList.model_validate_json(cached_user_watchlist)

        logger.debug(
            f"Список фильмов пользователя: {user_id=} для запроса: {page_size=}, {skip_page=} отсутствует в кэше"  # noqa: E501
        )

        fetched_watchlist = await self.repository.find(
            self.repository.collection.user_id == user_id, page_size=page_size, skip_page=skip_page
        )
        total_count_user_bookmarks = await self.repository.get_count(
            self.repository.collection.user_id == user_id
        )
        watchlist_result = FetchBookmarkList(
            user_id=user_id,
            total_count=total_count_user_bookmarks,
            on_page_count=len(fetched_watchlist),
            watchlist_page=[
                BookmarkObj(
                    film_id=bookmark.film_id,
                    comment=bookmark.comment,
                    created_at=bookmark.created_at,
                    updated_at=bookmark.updated_at,
                    status=bookmark.status,
                )
                for bookmark in fetched_watchlist
            ],
        )

        logger.info(
            f"Список фильмов пользователя: {user_id=} для запроса: {page_size=}, {skip_page=} найден в БД"  # noqa: E501
        )

        await self.cache.background_set(
            key=user_cache_key,
            value=watchlist_result.model_dump_json(),
            expire=app_config.cache_expire_in_seconds,
        )

        return watchlist_result

    async def update_bookmark_by_film_id(
        self, user_id: UUID, film_id: UUID, request_body: ChangeBookmarkRequest
    ) -> ChangeBookmarkResponse:

        await self.film_id_validator.validate_film_id(film_id)

        updated_bookmark = await self.repository.upsert(
            self.repository.collection.user_id == user_id,
            self.repository.collection.film_id == film_id,
            user_id=user_id,
            film_id=film_id,
            comment=request_body.comment,
            status=request_body.status,
        )

        if updated_bookmark:

            await self._invalidate_user_bookmark_cache(user_id)

            return ChangeBookmarkResponse(
                film_id=updated_bookmark.film_id,
                comment=updated_bookmark.comment,
                status=updated_bookmark.status,
                created_at=updated_bookmark.created_at,
                updated_at=updated_bookmark.updated_at,
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось добавить фильм в список просмотра",
        )

    async def _invalidate_user_bookmark_cache(self, user_id: UUID):
        user_cache_key = CACHE_KEY_USER_BOOKMARKS.format(user_id=user_id, page="*")
        await self.cache.background_destroy_all_by_pattern(pattern=user_cache_key)


@lru_cache()
def get_bookmark_service(
    cache: Cache = Depends(get_cache),
    repository: BookmarkRepository = Depends(get_bookmark_repository),
    film_id_validator: FilmIdValidator = Depends(get_film_id_validator),
    message_broker: AIOMessageBroker = Depends(get_broker_connector),
) -> BookmarkService:

    return BookmarkService(cache, repository, film_id_validator, message_broker)
