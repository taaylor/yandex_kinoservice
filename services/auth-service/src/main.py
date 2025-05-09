from api.v1.auth import auth_api
from api.v1.role import role
from api.v1.update_user_data import routers
from core.config import app_config
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from tracer_utils import init_tracer, request_id_middleware
from utils.connectors import lifespan
from utils.exceptions_handlers import setup_exception_handlers

app = FastAPI(
    title="Auth API для онлайн-кинотеатра",
    version="1.0.0",
    description="Сервис авторизации киносервиса",
    docs_url=app_config.docs_url,
    openapi_url=app_config.openapi_url,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# Подключение обработчиков
setup_exception_handlers(app)

if app_config.tracing:
    # Добавляем middleware
    app.middleware("http")(request_id_middleware)
    # Инициализация трейсера
    init_tracer(app, app_config.project_name)
    # Добавлене инструментария FastAPI для трейсов
    FastAPIInstrumentor.instrument_app(app)

SERVICE_PATH = "/auth/api/v1/"
app.include_router(role.router, prefix=f"{SERVICE_PATH}roles", tags=["Роли"])
app.include_router(routers.router, prefix=f"{SERVICE_PATH}users", tags=["Пользователи"])
app.include_router(auth_api.router, prefix=f"{SERVICE_PATH}sessions", tags=["Сессии"])
