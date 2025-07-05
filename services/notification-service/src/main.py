from api.v1.notification import notify_api
from core.config import app_config
from fastapi import FastAPI, responses
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from tracer_utils import init_tracer, request_id_middleware
from utils.connectors import lifespan
from utils.exceptions_handlers import setup_exception_handlers

app = FastAPI(
    title="Notification API для онлайн-кинотеатра",
    version="1.0.0",
    description="Сервис нотификации киносервиса",
    docs_url=app_config.docs_url,
    openapi_url=app_config.openapi_url,
    default_response_class=responses.ORJSONResponse,
    lifespan=lifespan,
)

setup_exception_handlers(app)

if app_config.tracing:
    app.middleware("http")(request_id_middleware)
    init_tracer(app, app_config.project_name)
    FastAPIInstrumentor.instrument_app(app)

SERVICE_PATH = "/notification/api/v1/"
app.include_router(notify_api.router, prefix=f"{SERVICE_PATH}notifications", tags=["Нотификации"])
