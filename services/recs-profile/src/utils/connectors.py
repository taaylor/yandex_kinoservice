import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from core.config import app_config
from db import postgres
from fastapi import FastAPI
from services.event_processor import create_recs_event_processor
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from utils.aiokafka_conn import create_consumer_manager

logger = logging.getLogger(__name__)


async def monitor_tasks(task: asyncio.Task[None], task_name: str) -> None:
    try:
        await task
    except asyncio.CancelledError:
        logger.info(f"Фоновая задача '{task_name}' была успешно отменена")
    except Exception as e:
        logger.error(f"Возникла ошибка при выполнении фоновой задачи '{task_name}': {e}")
        raise e


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

    # Создаём процессор для событий
    event_processor = create_recs_event_processor()

    # Создаём менеджер управления кафка консюмером
    kafka_manager = create_consumer_manager()
    await kafka_manager.start()
    consumer_tread = asyncio.create_task(
        # Передаю консюмеру функцию, которой нужно обрабатывать сообщения
        kafka_manager.consume_messages(event_processor.event_handler)
    )
    asyncio.create_task(monitor_tasks(consumer_tread, consumer_tread.get_name()))

    yield
    consumer_tread.cancel()

    try:
        await consumer_tread  # noqa: WPS476
    except asyncio.CancelledError:
        logger.info("Фоновая задача была успешно отменена")
    except Exception as e:
        logger.error(f"Возникла ошибка при завершении фонового процесса: {e}")

    await kafka_manager.stop()

    await engine.dispose()
