from typing import Generic, TypeVar

from db.postgres import Base
from sqlalchemy.ext.asyncio import AsyncSession
from utils.decorators import sqlalchemy_universal_decorator

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Базовый репозиторий для работы с хрвнилищем данных."""

    @sqlalchemy_universal_decorator
    async def create_all_objects(
        self,
        session: AsyncSession,
        objects: list[T],
    ) -> list[T]:
        session.add_all(objects)
        await session.flush()
        return objects

    @sqlalchemy_universal_decorator
    async def create_or_update_object(
        self,
        session: AsyncSession,
        object: T,
    ) -> T:
        obj = await session.merge(object)
        await session.flush()
        return obj
