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


class NotificationAPI(BaseModel):
    host: str = "localhost"
    port: int = 8002
    profile_path: str = "/notification/api/v1/notifications/mock-get-regular-mass-sending"

    @property
    def send_to_mass_notification_url(self) -> str:
        return f"http://{self.host}:{self.port}{self.profile_path}"


class Postgres(BaseModel):
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    db: str = "pg_db"

    @property
    def ASYNC_DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"  # noqa: WPS221, E501


class AppConfig(BaseSettings):
    glitchtip_url: str = "url"
    is_glitchtip_enabled: bool = False
    project_name: str = "event-generator"
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # noqa: WPS221
    docs_url: str = "/generator/openapi"
    openapi_url: str = "/generator/openapi.json"
    tracing: bool = False  # включение/выключение трассировки
    default_http_timeout: float = 3.0

    postgres: Postgres = Postgres()
    server: Server = Server()
    notification_api: NotificationAPI = NotificationAPI()

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
