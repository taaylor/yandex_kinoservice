from services.repository.notification_repository import NotificationRepository
from sqlalchemy.ext.asyncio import AsyncSession


class BaseService:
    def __init__(self, repository: NotificationRepository, session: AsyncSession) -> None:
        self.repository = repository
        self.session = session
