import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from core.config import app_config
from db import postgres
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    engine = create_async_engine(
        url=app_config.postgres.ASYNC_DATABASE_URL,
        echo=False,
        future=True,
    )
    postgres.async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield

    await engine.dispose()
