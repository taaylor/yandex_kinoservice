from db.postgres import Base
from services.repository.base_repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession


class BaseService:
    def __init__(self, repository: BaseRepository[Base], session: AsyncSession) -> None:
        self.repository = repository
        self.session = session
