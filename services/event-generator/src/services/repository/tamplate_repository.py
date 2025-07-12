from uuid import UUID

from models.models import Template
from services.repository.base_repository import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.decorators import sqlalchemy_universal_decorator


class TemplateRepository(BaseRepository):

    @sqlalchemy_universal_decorator
    async def fetch_template_by_id(
        self, session: AsyncSession, template_id: UUID
    ) -> Template | None:
        stmt = select(Template).where(Template.id == template_id)
        template = await session.execute(stmt)
        return template.scalar_one_or_none()


def get_template_repository() -> TemplateRepository:
    return TemplateRepository()
