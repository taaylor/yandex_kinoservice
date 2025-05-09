import logging
import os

import dotenv
from core.logger_config import LoggerSettings
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# Применяем настройки логирования
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


class Elastic(BaseModel):
    host: str = "localhost"
    port: int = 9200

    def get_es_host(self) -> str:
        return f"http://{self.host}:{self.port}"


class Redis(BaseModel):
    host: str = "localhost"
    port: int = 6379
    user: str = "redis_user"
    password: str = "Parol123"
    db: int = 0


class AppConfig(BaseSettings):
    project_name: str = "async-service"
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_url: str = "/async/openapi"
    openapi_url: str = "/async/openapi.json"
    cache_expire_in_seconds: int = 300
    tracing: bool = False  # включение/выключение трассировки

    elastic: Elastic = Elastic()
    redis: Redis = Redis()
    server: Server = Server()

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        case_sensitive=False,
        env_nested_delimiter="_",
        extra="ignore",
    )


def _get_config() -> AppConfig:
    # установка настроек для логов
    log = LoggerSettings()
    log.apply()

    app_config = AppConfig()
    logger.info(ENV_FILE)
    logger.info(f"app_config.initialized: {app_config.model_dump_json(indent=4)}")
    return app_config


app_config = _get_config()
