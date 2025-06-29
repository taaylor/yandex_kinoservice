import logging
from functools import lru_cache
from uuid import UUID

from fastapi import HTTPException, status
from models.models import (
    DictRoles,
    RolesPermissions,
    SocialAccount,
    User,
    UserCred,
    UserProfileSettings,
    UserSession,
    UserSessionsHist,
)
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from tracer_utils import traced
from utils.decorators import sqlalchemy_universal_decorator

logger = logging.getLogger(__name__)


class AuthRepository:
    @sqlalchemy_universal_decorator
    async def fetch_user_by_id(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @sqlalchemy_universal_decorator
    async def fetch_user_by_name(
        self,
        session: AsyncSession,
        username: str,
    ) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @sqlalchemy_universal_decorator
    async def fetch_user_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> User | None:
        stmt = select(User).join(UserCred).where(UserCred.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @sqlalchemy_universal_decorator
    async def fetch_usercred_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> UserCred | None:
        stmt = select(UserCred).where(UserCred.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @sqlalchemy_universal_decorator
    async def fetch_permissions_for_role(
        self,
        session: AsyncSession,
        role_code: str,
    ) -> list[str]:
        stmt = (
            select(RolesPermissions.permission).join(DictRoles).where(DictRoles.role == role_code)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @sqlalchemy_universal_decorator
    async def fetch_session_by_id(
        self,
        session: AsyncSession,
        session_id: UUID,
    ) -> UserSession:
        stmt = select(UserSession).where(UserSession.session_id == session_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @traced()
    @sqlalchemy_universal_decorator
    async def create_user_in_repository(
        self,
        session: AsyncSession,
        user: User,
        user_cred: UserCred,
        user_session: UserSession,
        user_session_hist: UserSessionsHist,
        user_settings: UserProfileSettings,
    ):
        session.add_all([user, user_cred, user_session, user_session_hist, user_settings])

    @traced()
    @sqlalchemy_universal_decorator
    async def create_session_in_repository(
        self,
        session: AsyncSession,
        user_session: UserSession,
        user_session_hist: UserSessionsHist,
    ):
        session.add_all([user_session, user_session_hist])

    @traced()
    @sqlalchemy_universal_decorator
    async def update_session_in_repository(
        self,
        session: AsyncSession,
        user_session: UserSession,
    ):
        stmt = (
            select(UserSession, UserSessionsHist)
            .join(
                UserSessionsHist,
                UserSession.session_id == UserSessionsHist.session_id,
            )
            .where(UserSession.session_id == user_session.session_id)
        )
        result = await session.execute(stmt)
        upd_user_session, upd_user_session_hist = result.one_or_none()

        # Проверяем, что обе сущности найдены. Если хотя бы одна отсутствует, выбрасываем ошибку.
        if not (upd_user_session and upd_user_session_hist):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Сессия не найдена",
            )

        upd_user_session.user_agent = user_session.user_agent
        upd_user_session.refresh_token = user_session.refresh_token
        upd_user_session.expires_at = user_session.expires_at

        upd_user_session_hist.user_agent = user_session.user_agent
        upd_user_session_hist.expires_at = user_session.expires_at

    @sqlalchemy_universal_decorator
    async def drop_session_by_id(self, session: AsyncSession, session_id: UUID):
        stmt = delete(UserSession).where(UserSession.session_id == session_id)
        await session.execute(stmt)

    @sqlalchemy_universal_decorator
    async def drop_sessions_except_current(
        self,
        session: AsyncSession,
        current_session: UUID,
        user_id: UUID,
    ) -> list[UUID]:
        stmt = (
            delete(UserSession)
            .where(UserSession.user_id == user_id)
            .where(UserSession.session_id != current_session)
            .returning(UserSession.session_id)
        )
        result = await session.execute(stmt)
        delete_sessions = result.scalars().all()
        return delete_sessions

    @traced()
    @sqlalchemy_universal_decorator
    async def fetch_history_sessions(
        self,
        session: AsyncSession,
        user_id: UUID,
        current_session: UUID,
        page_size: int,
        page_number: int,
    ) -> list[tuple]:
        skip_records = (page_number - 1) * page_size
        stmt = (
            select(
                UserSessionsHist.user_agent,
                UserSessionsHist.created_at,
                UserSessionsHist.session_id,
            )
            .where(UserSessionsHist.user_id == user_id)
            .where(UserSessionsHist.session_id != current_session)
            .order_by(UserSessionsHist.created_at.desc())
            .limit(page_size)
            .offset(skip_records)
        )
        result = await session.execute(stmt)
        data = result.all()

        return data

    @sqlalchemy_universal_decorator
    async def check_account_social(
        self,
        session: AsyncSession,
        social_id: str,
        social_name: str,
    ) -> SocialAccount:
        """Проверяет существование соц сети"""
        stmt = select(SocialAccount).where(
            SocialAccount.social_id == social_id,
            SocialAccount.social_name == social_name,
        )
        result = await session.execute(stmt)
        social_account = result.scalars().first()
        return social_account

    @sqlalchemy_universal_decorator
    async def drop_account_social_user(
        self,
        session: AsyncSession,
        social_name: str,
        user_id: UUID,
    ):
        stmt = (
            delete(SocialAccount)
            .where(SocialAccount.user_id == user_id)
            .where(SocialAccount.social_name == social_name)
        )

        result = await session.execute(stmt)
        return 1 if result.rowcount > 0 else 0

    @sqlalchemy_universal_decorator
    async def add_social_account(
        self,
        session: AsyncSession,
        social_account: SocialAccount,
    ):
        session.add(social_account)


@lru_cache
def get_auth_repository():
    return AuthRepository()
