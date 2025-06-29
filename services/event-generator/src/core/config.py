import logging
import os

import dotenv
from core.logger_config import LoggerSettings
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = dotenv.find_dotenv()

logger = logging.getLogger(__name__)


class Server(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    timeout: int = 30
    backlog: int = 512
    max_requests: int = 1000
    max_requests_jitter: int = 50
    worker_class: str = "uvicorn.workers.UvicornWorker"


class Redis(BaseModel):
    host: str = "localhost"
    port: int = 6379
    user: str = "redis_user"
    password: str = "Parol123"
    db: int = 0


class AppConfig(BaseSettings):
    glitchtip_url: str = "url"
    is_glitchtip_enabled: bool = False
    project_name: str = "event-generator"
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # noqa: WPS221
    docs_url: str = "/event-generator/openapi"
    openapi_url: str = "/event-generator/openapi.json"
    tracing: bool = False  # включение/выключение трассировки
    cache_expire_in_seconds: int = 300  # время кэширование ответа (сек.)
    default_http_timeout: float = 3.0

    redis: Redis = Redis()
    server: Server = Server()

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        case_sensitive=False,
        env_nested_delimiter="_",
        extra="ignore",
    )


def _get_config() -> AppConfig:
    log = LoggerSettings()
    log.apply()

    app_config = AppConfig()
    logger.info(f"app_config.initialized: {app_config.model_dump_json(indent=4)}")
    return app_config


app_config = _get_config()
