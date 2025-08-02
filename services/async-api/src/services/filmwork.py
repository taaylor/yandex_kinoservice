import json
import logging
import math
from functools import lru_cache
from typing import Any
from uuid import UUID

from api.v1.filmwork.schemas import FilmDetailResponse, FilmListResponse, FilmSorted, FilmsType
from api.v1.internal.schemas import FilmInternalResponse
from auth_utils import Permissions
from core.config import app_config
from db.cache import Cache, get_cache
from db.database import PaginateBaseDB
from db.elastic import get_paginate_repository
from fastapi import Depends, HTTPException, status
from models.schemas_logic import FilmLogic, PeriodEnum
from pydantic import TypeAdapter
from suppliers.rec_profile import RecProfileSupplier, get_rec_profile_supplier
from suppliers.statistic_supplier import StatisticSupplier, get_statistic_supplier
from tracer_utils import traced

logger = logging.getLogger(__name__)


REDIS_KEY_FILMS = "films:"
REDIS_KEY_REC_FILMS = "films:rec:{user_id}:{page_number}:{page_size}"
REDIS_TRENDS_FILMS = "films:trends:{period}:{page_size}"
REDIS_FILMS_CACHE_EXPIRES = app_config.cache_expire_in_seconds


class FilmRepository:
    """Класс для работы с хранилищем ElasticSearch"""

    FILMS_INDEX_ES = "movies"

    def __init__(self, repository: PaginateBaseDB):
        self.repository = repository

    async def get_film_by_id(self, film_id: UUID) -> FilmLogic | None:
        """Получить детальную информацию о фильме из ElasticSearch по UUID"""
        logger.debug(
            f"Получаю детальную информацию из ElasticSearch по фильму {film_id=}",
        )

        film = await self.repository.get_object_by_id(
            index=self.FILMS_INDEX_ES,
            object_id=film_id,
        )

        if film:
            film = FilmLogic.model_validate(film)

        return film

    async def get_list_film(
        self,
        sort: FilmSorted,
        genre: list[UUID],
        page_size: int,
        page_number: int,
        categories: list[str],
    ) -> list[FilmLogic]:
        """Получить список фильмов из ElasticSearch по фильтрации переданных данных"""
        sort_ = (
            [{sort.value[1:]: "desc"}] if sort.value.startswith("-") else [{sort.value[:]: "asc"}]
        )

        query = {
            "sort": sort_,
            "query": {
                "bool": {
                    "filter": [{"terms": {"type": categories}}],
                },
            },
        }

        if genre:
            genre_ids = [str(g) for g in genre]
            should = [
                {
                    "nested": {
                        "path": "genres",
                        "query": {
                            "bool": {"must": [{"terms": {"genres.id": genre_ids}}]},
                        },
                    },
                },
            ]
            query["query"]["bool"]["should"] = should
            query["query"]["bool"]["minimum_should_match"] = 1

        found_films = await self._search_films(
            query_search=query,
            page_size=page_size,
            page_number=page_number,
        )
        return found_films

    async def get_list_film_by_ids(self, film_ids: list[UUID]) -> list[FilmLogic]:
        """Получить список фильмов из ElasticSearch по списку film_id"""
        film_ids_str_list = [str(film_id) for film_id in film_ids]
        query = {
            "query": {
                "bool": {
                    "filter": [{"terms": {"id": film_ids_str_list}}],
                },
            },
        }

        found_films = await self._search_films(query_search=query, page_size=1000, page_number=1)
        return found_films

    async def get_list_film_by_query(
        self,
        query: str,
        page_size: int,
        page_number: int,
        categories: list[str],
    ) -> list[FilmLogic]:
        """Получить список фильмов из ElasticSearch по поисковому запросу"""
        # Фильтрация работает по нижнему регистру из-за особенностей хранения в ES

        query_search = {
            "query": {
                "bool": {
                    "filter": [{"terms": {"type": categories}}],
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [
                                    "title^6",
                                    "description^5",
                                    "genres_names^4",
                                    "directors_names^3",
                                    "actors_names^4",
                                    "writers_names^3",
                                ],
                                "type": "best_fields",
                                "operator": "or",
                                "fuzziness": "AUTO",
                                "minimum_should_match": "75%",
                            },
                        },
                        {
                            "match_phrase": {
                                "title": {"query": query, "boost": 3, "slop": 3},
                            },
                        },
                        {
                            "match_phrase": {
                                "description": {"query": query, "boost": 2, "slop": 3},
                            },
                        },
                    ],
                    "minimum_should_match": 1,
                },
            },
        }

        found_films = await self._search_films(
            query_search=query_search,
            page_size=page_size,
            page_number=page_number,
        )
        return found_films

    async def _search_films(
        self,
        query_search: dict[str, Any],
        page_size: int,
        page_number: int,
    ) -> list[FilmLogic]:
        """Сделать запрос в ElasticSearch на получение списка фильмов"""
        films = await self.repository.get_list(
            index=self.FILMS_INDEX_ES,
            body=query_search,
            page_size=page_size,
            page_number=page_number,
        )

        if not films:
            logger.error(
                "В результате запроса по фильмам в ElasticSearch ничего не нашлось",
            )
            return []

        film_list = [FilmLogic.model_validate(film) for film in films]

        logger.info(
            f"В результате запроса по фильмам в ElasticSearch найдено: {len(film_list)} - фильмов",
        )
        return film_list

    async def get_total_films(self, categories: list[str]) -> int:
        """Получить количество фильмов из Elasticsearch"""
        logger.debug(
            "Делаю запрос на получение количества фильмов из ElasticSearch, "
            + "в кеше данных не оказалось...",
        )

        total = await self.repository.get_count(
            index=self.FILMS_INDEX_ES,
            categories=categories,
        )
        logger.info(
            f"Получено количество фильмов {total=}, сохраняю результат в кеш. Тип {categories}",
        )
        return total

    async def search_film_by_vector_in_db(
        self, vector: list[float], page_size: int = 50, page_number: int = 1
    ) -> list[FilmLogic]:
        """
        Выполняет векторный knn-поиск в Elasticsearch по полю `embedding`,
         исключая фильмы со статусом ARCHIVED.

        :param vector: Эмбеддинг‑вектор запроса (список из 384 float-значений).
        :param page_size: Количество фильмов на одной странице результатов.
        :param page_number: Номер страницы для пагинации (начиная с 1).
        :return: Список объектов `FilmLogic` для найденных фильмов;
                 пустой список, если по векторному поиску не найдено ни одного фильма.
        """
        # Секции запроса:
        #  - knn - выполняет приближённый поиск ближайших соседей (approximate kNN)
        # по HNSW‑графу в поле embedding
        #  - filter внутри knn - исключает из рассмотрения документы
        # с type = ARCHIVED до обхода HNSW‑графа
        #  - rescore - для уже найденных k кандидатов берёт первые window_size (10)
        # и точно пересчитывает их сходство скриптом:
        # cosineSimilarity(params.query_vector, 'embedding') + 1.0
        # скрипт устраняет мелкие погрешности приближённого kNN‑поиска
        # и даёт точный порядок самых релевантных документов.
        body_query = {
            "knn": {
                "field": "embedding",  # embedding - имя поля‑вектора
                "query_vector": vector,  # запросный 384‑мерный вектор
                "k": page_size * page_number,  # топ‑K ближайших вернуть
                # num_candidates - сколько узлов HNSW обойти чем больше,
                # тем глубже обход графа — выше шанс найти хоть что‑то
                "num_candidates": 100,
                # секция filter убирает архивные фильмы, выполняется до приска по вектору
                "filter": {"bool": {"must_not": {"term": {"type": FilmsType.ARCHIVED.value}}}},
            },
            "rescore": {
                "window_size": 10,
                "query": {
                    "rescore_query": {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                #  вычисляет косинусное сходство между переданным
                                # в параметре query_vector вектором запроса
                                # и вектором, хранящимся в поле документа embedding
                                "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",  # noqa: E501
                                "params": {"query_vector": vector},
                            },
                        }
                    }
                },
            },
        }
        logger.debug(
            (
                "FilmRepository.search_film_by_vector_in_db:"
                " начинаем выполнять запрос в Elasticsearch,"
                f" тело запроса {body_query}"
            ),
        )
        films = await self.repository.get_list(
            index=self.FILMS_INDEX_ES,
            body=body_query,
            page_number=page_number,
            page_size=page_size,
        )
        if not films:
            logger.info(
                (
                    "FilmRepository.search_film_by_vector_in_db:"
                    " В результате запроса по векторному поиску в ElasticSearch"
                    " ничего не нашлось"
                ),
            )
            return []
        logger.info(
            (
                "FilmRepository.search_film_by_vector_in_db:"
                " В результате запроса по векторному поиску в ElasticSearch"
                f" нашлось {len(films)} фильмов"
                f" с учётом page_size={page_size} и page_number={page_number}"
            ),
        )
        films_in_schema = [FilmLogic.model_validate(film) for film in films]
        return films_in_schema

    async def search_film_by_list_vector(
        self, vectors: list[list[float]], page_size: int, page_number: int
    ) -> list[FilmLogic]:
        """
        Выполняет запрос по нескольким векторам,
        отдает фильмы найденные по среднему косинусному сходству
        """

        params = {}
        source = []
        dims = app_config.embedding_dims

        for idx, vector in enumerate(vectors, start=1):
            if dims == len(vector):
                source.append(f"cosineSimilarity(params.query_vector{idx}, 'embedding')")
                params[f"query_vector{idx}"] = vector

        query = {
            "query": {
                "script_score": {
                    "query": {
                        "bool": {
                            "must_not": {"term": {"type": FilmsType.ARCHIVED.value}},
                            "filter": {"exists": {"field": "embedding"}},
                        },
                    },
                    "script": {
                        "source": f"""
                            double score = ({" + ".join(source)}) / {len(source)};
                            return Math.max(score, 0);
                        """,
                        "params": params,
                    },
                }
            }
        }

        films_db = await self.repository.get_list(
            index=self.__class__.FILMS_INDEX_ES,
            body=query,
            page_number=page_number,
            page_size=page_size,
        )

        logger.info(
            f"Из хранилища получено {len(films_db)} фильмов на основе {len(vectors)} векторов"
        )

        if films_db:
            return [FilmLogic.model_validate(film) for film in films_db]
        return []


class FilmService:
    """Класс, реализующий бизнес-логику работы с фильмами."""

    __slots__ = ("cache", "repository", "rec_profile_supplier", "statistic_supplier")

    def __init__(
        self,
        cache: Cache,
        repository: FilmRepository,
        rec_profile_supplier: RecProfileSupplier,
        statistic_supplier: StatisticSupplier,
    ):
        self.cache = cache
        self.repository = repository
        self.rec_profile_supplier = rec_profile_supplier
        self.statistic_supplier = statistic_supplier

    async def get_film_by_id(
        self,
        film_id: UUID,
        user_permissions: set[str],
    ) -> FilmDetailResponse | None:
        """Получить детальную информацию о фильме по UUID."""
        cached_data = await self.cache.get(key=str(film_id))

        if cached_data:
            logger.debug(f"Фильм {film_id} найден в кеше.")
            film = FilmDetailResponse.model_validate_json(cached_data)
            if not self._validate_film_for_user(film.type, user_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав для получения этого фильма",
                )
            return film

        film = await self.repository.get_film_by_id(film_id=film_id)

        if film is None:
            return film

        film_dto = FilmDetailResponse.transform_from_FilmLogic(film)

        await self.cache.background_set(
            key=str(film_id),
            value=film_dto.model_dump_json(),
            expire=REDIS_FILMS_CACHE_EXPIRES,
        )

        if not self._validate_film_for_user(film_dto.type, user_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для получения этого фильма",
            )
        return film_dto

    @traced("get_list_film_process")
    async def get_list_film(
        self,
        sort: FilmSorted,
        genre: list[UUID],
        page_size: int,
        page_number: int,
        user_permissions: set[str],
    ) -> list[FilmListResponse]:
        """Получить список фильмов с фильтрацией."""
        categories = sorted(self._get_categories_for_permissions(user_permissions))
        genre_key = f":genres{'-'.join(str(g) for g in sorted(set(genre)))}" if genre else ""
        cache_key = (
            f"{REDIS_KEY_FILMS}{sort.value}"
            f":page{page_number}"
            f":size{page_size}{genre_key}"
            f":{'-'.join(categories)}"
        )
        cached_data = await self.cache.get(key=cache_key)

        if cached_data:
            logger.info("Список фильмов найден в кеше.")
            films_list = [FilmListResponse.model_validate(film) for film in json.loads(cached_data)]
            return films_list

        films = await self.repository.get_list_film(
            sort=sort,
            genre=genre,
            page_size=page_size,
            page_number=page_number,
            categories=categories,
        )

        if not films:
            return []

        films_list = [
            FilmListResponse(
                uuid=film.id,
                title=film.title,
                imdb_rating=film.imdb_rating,
                type=film.type,
            )
            for film in films
        ]

        json_films = json.dumps([film.model_dump(mode="json") for film in films_list])
        await self.cache.background_set(
            key=cache_key,
            value=json_films,
            expire=REDIS_FILMS_CACHE_EXPIRES,
        )
        return films_list

    async def get_total_pages(self, page_size: int, user_permissions: set[str]) -> int:
        """Получить количество доступных страниц для пагинации."""
        logger.debug("Запрашиваю общее количество страниц для фильмов...")
        categories = sorted(self._get_categories_for_permissions(user_permissions))
        total_films_cache_key = f"{REDIS_KEY_FILMS}total:{'-'.join(categories)}"

        total_films = await self.cache.get(key=total_films_cache_key)
        if total_films is None:
            logger.info("Общее количество фильмов не найдено в кеше, делаю запрос...")

            total_films = await self.repository.get_total_films(categories)

            if not total_films or total_films == 0:
                return 0

            await self.cache.background_set(
                key=total_films_cache_key,
                value=str(total_films),
                expire=REDIS_FILMS_CACHE_EXPIRES,
            )

        total_pages = math.ceil(int(total_films) / page_size)
        logger.info(f"Найдено {total_pages} страниц фильмов.")

        return total_pages

    async def get_list_film_by_search_query(
        self,
        query: str,
        page_size: int,
        page_number: int,
        user_permissions: set[str],
    ) -> list[FilmListResponse]:
        """Получить список фильмов по поисковому запросу."""
        categories = sorted(self._get_categories_for_permissions(user_permissions))

        films = await self.repository.get_list_film_by_query(
            query=query,
            page_size=page_size,
            page_number=page_number,
            categories=categories,
        )

        if films:
            return [
                FilmListResponse(
                    uuid=film.id,
                    title=film.title,
                    imdb_rating=film.imdb_rating,
                    type=film.type,
                )
                for film in films
            ]

        return films

    def _validate_film_for_user(
        self,
        film_type: str,
        user_permissions: set[str],
    ) -> bool:
        logger.debug(
            f"Получен фильм для проверки: {film_type}, права пользователя {user_permissions}",
        )
        if (
            film_type == FilmsType.ARCHIVED.value
            and Permissions.CRUD_FILMS.value in user_permissions
        ):
            return True
        if film_type == FilmsType.PAID.value and (
            Permissions.PAID_FILMS.value in user_permissions
            or Permissions.CRUD_FILMS.value in user_permissions
        ):
            return True
        if film_type == FilmsType.FREE.value:
            return True
        return False

    def _get_categories_for_permissions(self, user_permissions: set[str]) -> list[str]:
        if Permissions.CRUD_FILMS.value in user_permissions:
            return [
                FilmsType.PAID.value,
                FilmsType.ARCHIVED.value,
                FilmsType.FREE.value,
            ]
        if Permissions.PAID_FILMS.value in user_permissions:
            return [FilmsType.PAID.value, FilmsType.FREE.value]
        if Permissions.FREE_FILMS.value in user_permissions:
            return [FilmsType.FREE.value]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для получения этого фильма",
        )

    async def get_films_by_id_internal(
        self,
        film_ids: list[UUID],
    ) -> list[FilmInternalResponse]:
        """Получить детальную информацию о фильме по UUID."""

        films_from_db = await self.repository.get_list_film_by_ids(film_ids=film_ids)
        films = [FilmInternalResponse.transform_from_FilmLogic(film) for film in films_from_db]

        return films

    async def get_films_by_vector(
        self,
        vector: list[float],
        page_size: int = 50,
        page_number: int = 1,
    ) -> list[FilmListResponse]:
        """
        Ищет фильмы по семантическому embedding-вектору с постраничной навигацией.

        :param vector: Эмбеддинг‑вектор запроса (список из 384 float-значений).
        :param page_size: Количество фильмов в одной странице результатов.
        :param page_number: Номер страницы (начиная с 1).
        :return: Список `FilmListResponse` с полями:
                 - uuid: идентификатор фильма,
                 - title: название,
                 - imdb_rating: рейтинг IMDB,
                 - type: тип (PAID/FREE).
                 Пустой список, если по вектору никаких фильмов не найдено.
        """
        logger.debug(
            (
                "FilmService.get_films_by_vector:"
                " поступил запрос поиска по вектору,"
                f" vector: {vector}"
                f" page_size={page_size}, page_number={page_number}"
            )
        )
        films_from_db = await self.repository.search_film_by_vector_in_db(
            vector=vector, page_size=page_size, page_number=page_number
        )
        films = [
            FilmListResponse(
                uuid=film.id,
                title=film.title,
                imdb_rating=film.imdb_rating,
                type=film.type,
            )
            for film in films_from_db
        ]
        logger.info(
            (
                "FilmService.get_films_by_vector:"
                " запрос успешно отработал,"
                f" vector: {vector}"
                f" page_size={page_size}, page_number={page_number}"
            )
        )
        return films

    async def get_recommended_films(
        self, user_id: UUID, page_size: int, page_number: int
    ) -> list[FilmListResponse]:
        """Возвращает рекомендации пользователя"""

        type_adapter = TypeAdapter(list[FilmListResponse])
        key_cache = REDIS_KEY_REC_FILMS.format(
            user_id=user_id, page_number=page_number, page_size=page_size
        )

        if rec_films_cache := await self.cache.get(key_cache):
            logger.debug(f"Для пользователя {user_id=} найдены рекомендации в кеше")
            return type_adapter.validate_json(rec_films_cache)

        logger.debug(f"Рекомендаций пользователя {user_id=} в кеше не оказалось")
        user_embeddings = await self.rec_profile_supplier.fetch_rec_profile_user(user_id)
        if not user_embeddings:
            return []

        rec_films_db = await self.repository.search_film_by_list_vector(
            vectors=user_embeddings, page_size=page_size, page_number=page_number
        )

        logger.info(f"Для пользователя {user_id=} найдено {len(rec_films_db)} рекомендаций")

        if rec_films_db:
            films_dto = [
                FilmListResponse(
                    uuid=film.id,
                    title=film.title,
                    imdb_rating=film.imdb_rating,
                    type=film.type,
                )
                for film in rec_films_db
            ]
            await self.cache.background_set(
                key=key_cache,
                value=type_adapter.dump_json(films_dto),
                expire=REDIS_FILMS_CACHE_EXPIRES,
            )
            return films_dto
        return []

    async def get_trends_films(self, period: PeriodEnum, page_size: int) -> list[FilmListResponse]:
        type_adapter = TypeAdapter(list[FilmListResponse])
        key_cache = REDIS_TRENDS_FILMS.format(period=period.value, page_size=page_size)
        if trends_films_cache := await self.cache.get(key_cache):
            logger.debug(f"По ключу {key_cache} найдены в кеше трендовые фильмы")
            return type_adapter.validate_json(trends_films_cache)

        trends_films_ids = await self.statistic_supplier.fetch_trends_films(
            page_size=page_size, period=period
        )
        trends_films_db = await self.repository.get_list_film_by_ids(film_ids=trends_films_ids)

        if trends_films_db:
            logger.info(f"Получено {len(trends_films_db)} трендовых фильмов")
            trends_films = [
                FilmListResponse(
                    uuid=film.id,
                    title=film.title,
                    imdb_rating=film.imdb_rating,
                    type=film.type,
                )
                for film in trends_films_db
            ]
            await self.cache.background_set(
                key=key_cache,
                value=type_adapter.dump_json(trends_films),
                expire=REDIS_FILMS_CACHE_EXPIRES,
            )
            return trends_films
        return []


@lru_cache
def get_film_service(
    cache: Cache = Depends(get_cache),
    repository: PaginateBaseDB = Depends(get_paginate_repository),
    rec_profile_supplier: RecProfileSupplier = Depends(get_rec_profile_supplier),
    statistic_supplier: StatisticSupplier = Depends(get_statistic_supplier),
) -> FilmService:
    """Получить экземпляр класса FilmService"""
    film_repository = FilmRepository(repository)
    return FilmService(cache, film_repository, rec_profile_supplier, statistic_supplier)
