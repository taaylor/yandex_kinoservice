import logging
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

import backoff
from beanie import Document
from core.config import app_config
from models.enum_models import SortedEnum
from utils.decorators import mongodb_handler_exceptions

logger = logging.getLogger(__name__)


class BaseRepository[T: Document]:  # noqa: WPS214
    """
    Базовый репозиторий для работы с Beanie документами.

    Generic класс, где T - тип документа, с которым будет работать класс, наследник beanie.Document.
    """

    __slots__ = ("collection",)

    def __init__(self, model: type[T]):
        """
        Инициализирует репозиторий с указанной Beanie-моделью.

        :param model: Класс модели, наследник beanie.Document.
        """

        self.collection: type[T] = model

    @backoff.on_exception(backoff.expo, app_config.mongodb.base_connect_exp)
    @mongodb_handler_exceptions
    async def get_document(self, *filters: Any) -> T | None:
        """
        Находит один документ по переданным фильтрам.

        :param filters: Условия поиска, например Model.user_id == user_id, Model.film_id == film_id
        :return: Экземпляр модели Document или None, если не найден.
        """
        logger.debug(f"Поиск документа по фильтрам {filters}.")
        return await self.collection.find_one(*filters)

    @backoff.on_exception(backoff.expo, app_config.mongodb.base_connect_exp)
    @mongodb_handler_exceptions
    async def insert_document(self, **insert_data: Any) -> T:
        """
        Создаёт новый документ.

        :param insert_data: Поля для создания документа,
                            например user_id=user_id, film_id=film_id, score=score.
        :return: Вставленный экземпляр модели Document.
        """

        logger.debug(f"Создание документа с данными {insert_data}.")
        return await self.collection(**insert_data).insert()

    @backoff.on_exception(backoff.expo, app_config.mongodb.base_connect_exp)
    @mongodb_handler_exceptions
    async def update_document(self, document: T, **update_data: Any) -> T:
        """
        Обновляет поля в переданном экземпляре документа и сохраняет.

        :param document: Ранее полученный экземпляр модели.
        :param update_data: Поля и новые значения для обновления, например score=new_score.
        :return: Обновлённый экземпляр модели Document.
        """

        logger.debug(f"Обновление документа с данными {update_data}.")
        update_field = set(update_data.keys())
        for field in update_field:
            if hasattr(document, field):
                setattr(document, field, update_data[field])
        document.updated_at = datetime.now(timezone.utc)  # type: ignore
        return await document.save()

    @backoff.on_exception(backoff.expo, app_config.mongodb.base_connect_exp)
    @mongodb_handler_exceptions
    async def upsert(self, *filters: Any, **insert_data: Any) -> T:
        """
        Если документ по фильтрам найден — обновляет его полями из insert_data,
        иначе — создаёт новый документ с переданными данными.

        :param filters: Условия поиска для существующего документа,
                        например Model.user_id == user_id.
        :param insert_data: Поля для вставки или обновления,
                            например user_id=user_id, film_id=film_id, score=score.
        :return: Экземпляр модели Document после операции.
        """

        existing_document = await self.get_document(*filters)
        logger.debug(
            "Обновление/создание документа.\n"
            f" Поиск по фильтрам {filters}.\n"
            f" Создание/обновление документа с данными {insert_data}."
        )
        if existing_document:
            return await self.update_document(existing_document, **insert_data)
        else:
            return await self.insert_document(**insert_data)

    @backoff.on_exception(backoff.expo, app_config.mongodb.base_connect_exp)
    @mongodb_handler_exceptions
    async def delete_document(self, *filters: Any) -> bool:
        """
        Удаляет один документ по переданным фильтрам.

        :param filters: Условия поиска для удаления,
                        например Model.user_id == user_id, Model.film_id == film_id.
        :return: True, если документ найден и удалён; False, если не найден.
        """

        existing_document = await self.get_document(*filters)
        if existing_document:
            await existing_document.delete()
            logger.debug(f"Документ по фильтрам {filters} найден и удалён.")
            return True
        logger.debug(f"Документ по фильтрам {filters} не найден и не может быть удалён.")
        return False

    @backoff.on_exception(backoff.expo, app_config.mongodb.base_connect_exp)
    @mongodb_handler_exceptions
    async def find(
        self,
        *filters: Any,
        page_size: int = 50,
        skip_page: int = 0,
        sorted: SortedEnum = SortedEnum.CREATED_DESC,
    ) -> list[Document]:
        """
        Получает список объектов с пагинацией и сортировкой на уровне БД.

        :param filters: Условия поиска,
                        например Model.user_id == user_id, Model.film_id == film_id.
        :param skip_page: Количество страниц, которые необходимо пропустить при выдаче.
        :param page_size: Размер одной страницы
        :return: Список документов с учётом пагинации и сортировкой.
        """
        logger.debug(f"Поиск записей в БД по критериям: {filters}, {skip_page=}, {page_size=} ")

        skip_count = skip_page * page_size

        result = (
            await self.collection.find(*filters)  # noqa: WPS221
            .sort(sorted.value)
            .skip(skip_count)
            .limit(page_size)
            .to_list()
        )
        logger.debug(
            f"Получен список документов {self.collection.__name__} в количестве: {len(result)}"
        )

        return result

    @backoff.on_exception(backoff.expo, app_config.mongodb.base_connect_exp)
    @mongodb_handler_exceptions
    async def get_count(self, *filters: Any) -> int:
        """Возвращает количество документов в коллекции по заданным фильтрам"""
        return await self.collection.find(*filters).count()


@lru_cache()
def get_rating_repository(model: type[Document]) -> BaseRepository[Document]:
    return BaseRepository(model)
