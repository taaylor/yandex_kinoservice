from api.v1.filmwork import filmwork
from api.v1.genre import genres
from api.v1.person import persons
from core.config import app_config
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from tracer_utils import init_tracer, request_id_middleware
from utils import exceptions_handlers
from utils.connectors import lifespan

app = FastAPI(
    title="Read-only API для онлайн-кинотеатра",
    description="Информация о кинопроизведениях, жанрах и персонах, "
    "участвовавших в создании произведения",
    version="1.0.0",
    # Адрес документации в красивом интерфейсе
    docs_url=app_config.docs_url,
    # Адрес документации в формате OpenAPI
    openapi_url=app_config.openapi_url,
    # заменяем стандартный JSON-сериализатор на более шуструю версию, написанную на Rust
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)


# Подключение обработчиков
exceptions_handlers.setup_exception_handlers(app)

if app_config.tracing:
    # Добавляем middleware
    app.middleware("http")(request_id_middleware)
    # Инициализация трейсера
    init_tracer(app, app_config.project_name)
    # Добавлене инструментария FastAPI для трейсов
    FastAPIInstrumentor.instrument_app(app)

# Секция подключения роутеров к серверу
SERVICE_PATH = "/async/api/v1/"
app.include_router(filmwork.router, prefix=f"{SERVICE_PATH}films", tags=["Фильмы"])
app.include_router(persons.router, prefix=f"{SERVICE_PATH}persons", tags=["Персоны"])
app.include_router(genres.router, prefix=f"{SERVICE_PATH}genres", tags=["Жанры"])
