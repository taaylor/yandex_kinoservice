import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from core.config import app_config
from db import cache, postgres, rabbitmq
from fastapi import FastAPI
from redis.asyncio import Redis
from services.processors.delayed_notification_processor import get_delayed_notification_processor
from services.processors.mass_notify_processors import (
    get_mass_notify_etl_processor,
    get_mass_notify_status_processor,
)
from services.processors.single_notification_processor import get_new_notification_processor
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:  # noqa: WPS217, WPS210, WPS213
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

    cache.cache_conn = Redis(
        host=app_config.redis.host,
        port=app_config.redis.port,
        db=app_config.redis.db,
        decode_responses=True,
        username=app_config.redis.user,
        password=app_config.redis.password,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_error=False,
        retry_on_timeout=False,
    )

    # Создаём сессию к RabbitMQ сначала
    await rabbitmq.get_producer()

    # Запускаем фоновые задачи после инициализации RabbitMQ
    new_notify_processor = await get_new_notification_processor()
    delayed_notify_processor = await get_delayed_notification_processor()
    mass_notify_status_processor = get_mass_notify_status_processor()
    mass_notify_etl_processor = await get_mass_notify_etl_processor()

    background_tasks = [
        asyncio.create_task(
            mass_notify_etl_processor.process_mass_notify_etl(), name="Mass Notify ETL Processor"
        ),
        asyncio.create_task(
            mass_notify_status_processor.process_mass_notify_new_status(),
            name="Mass Notify Status Processor - New",
        ),
        asyncio.create_task(
            mass_notify_status_processor.process_mass_notify_delayed_status(),
            name="Mass Notify Status Processor - Delayed",
        ),
        asyncio.create_task(
            new_notify_processor.process_new_notifications(), name="New Notification Processor"
        ),
        asyncio.create_task(
            delayed_notify_processor.process_delayed_notifications(),
            name="Delayed Notification Processor",
        ),
    ]

    # Мониторим фоновые задачи
    for task in background_tasks:
        asyncio.create_task(monitor_tasks(task, task.get_name()))

    yield

    # Отменяем все фоновые задачи при завершении
    for task in background_tasks:
        task.cancel()

    for task in background_tasks:
        try:
            await task  # noqa: WPS476
        except asyncio.CancelledError:
            logger.info("Фоновая задача была успешно отменена")
        except Exception as e:
            logger.error(f"Возникла ошибка при завершении фонового процесса: {e}")

    await engine.dispose()
    await cache.cache_conn.close()

    if rabbitmq.producer:
        await rabbitmq.producer.close()
