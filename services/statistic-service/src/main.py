from api.v1 import statistic_api
from core.config import app_config
from fastapi import FastAPI, responses
from utils.connectors import lifespan
from utils.exceptions_handlers import setup_exception_handlers

app = FastAPI(
    version="1.0.0",
    title="Сервис статистики киносервиса",
    description=(
        "Сервис напрямую работает с колоночной бд ClickHouse, "
        "который позволяет получить необходимые данные, "
        "на основе метрик пользователей"
    ),
    docs_url=app_config.docs_url,
    openapi_url=app_config.openapi_url,
    default_response_class=responses.ORJSONResponse,
    lifespan=lifespan,
)

setup_exception_handlers(app)

SERVICE_PATH = "/statistic/api/v1/"
app.include_router(
    statistic_api.router, prefix=f"{SERVICE_PATH}trends", tags=["Получение трендовых, объектов"]
)
