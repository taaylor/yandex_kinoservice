import asyncio
import logging

from aiohttp import ClientSession, web
from core.config import app_config
from redis.asyncio import Redis
from services.processors.event_handler import EventHandler, get_event_handler
from services.processors.supplier_processor import SupplierProcessor, get_supplier_processor
from services.ws_service import WebSocketHandlerService, get_websocket_handler_service
from storage import cache
from storage.messagebroker import AsyncMessageBroker, get_message_broker

logger = logging.getLogger(__name__)


async def monitor_task(task: asyncio.Task[None], name: str):
    """Мониторит выполнение задачи и отлавливает исключения."""
    try:
        await task
    except asyncio.CancelledError:
        logger.info(f"{name} был отменён")
    except Exception as e:
        logger.error(f"Ошибка в {name}: {e}")
        raise


async def setup_dependencies(app: web.Application):  # noqa: WPS210, WPS213
    """Инициализирует зависимости при старте приложения"""

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

    cache_manager: cache.Cache = cache.get_cache()
    event_handler: EventHandler = get_event_handler(cache_manager)
    websocket_handler_service: WebSocketHandlerService = get_websocket_handler_service(
        cache_manager
    )
    message_broker: AsyncMessageBroker = get_message_broker()
    client_session: ClientSession = ClientSession()
    supplier_processor: SupplierProcessor = get_supplier_processor(
        cache=cache_manager, client_session=client_session
    )

    consumer_task = asyncio.create_task(
        message_broker.consumer(
            queue_name=app_config.rabbitmq.review_like_queue,
            callback=event_handler.event_handler,
        ),
        name="message_broker_consumer",
    )
    logger.info("Consumer rabbitmq запущен в фоновом режиме")
    asyncio.create_task(monitor_task(consumer_task, "message_broker_consumer"))

    supplier_task = asyncio.create_task(
        supplier_processor.supplier_processor(), name="supplier_processor"
    )
    logger.info("Supplier процесс запущен в фоновом режиме")

    asyncio.create_task(monitor_task(consumer_task, "message_broker_consumer"))
    asyncio.create_task(monitor_task(supplier_task, "supplier_processor"))

    app.setdefault("cache_conn", cache.cache_conn)
    app.setdefault("cache_manager", cache_manager)
    app.setdefault("message_broker", message_broker)
    app.setdefault("websocket_handler_service", websocket_handler_service)
    app.setdefault("client_session", client_session)


async def cleanup_dependencies(app: web.Application):  # noqa: WPS213
    """Закрывает все активные зависимости при остановке приложения"""

    message_broker: AsyncMessageBroker = app.get("message_broker")
    cache_conn: Redis = app.get("cache_conn")
    client_session: ClientSession = app.get("client_session")

    if cache_conn:
        await cache_conn.close()

    if message_broker:
        await message_broker.close()

    if client_session:
        await client_session.close()

    try:
        tasks = asyncio.all_tasks()
        for task in tasks:
            task.cancel()
        await asyncio.sleep(0)
    except asyncio.CancelledError:
        logger.info("Все фоновые задачи отменены")
