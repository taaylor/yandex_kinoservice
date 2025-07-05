from aiohttp import web
from api.v1 import ws_sender
from utils.connectors import (
    cleanup_cache,
    cleanup_message_broker,
    setup_cache,
    setup_message_broker,
)


def start_application() -> web.Application:
    """
    Фабрика инициализации приложения
    """
    app = web.Application()
    app.add_routes(ws_sender.routes)
    app.on_startup.append(setup_cache)
    app.on_startup.append(setup_message_broker)
    app.on_cleanup.append(cleanup_message_broker)
    app.on_cleanup.append(cleanup_cache)
    return app


app = start_application()
