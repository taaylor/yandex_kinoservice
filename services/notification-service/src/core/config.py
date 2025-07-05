import logging

import dotenv
from core.logger_config import LoggerSettings
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = dotenv.find_dotenv()


class Server(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    timeout: int = 30
    backlog: int = 512
    max_requests: int = 1000
    max_requests_jitter: int = 50
    worker_class: str = "uvicorn.workers.UvicornWorker"


class Postgres(BaseModel):
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    db: str = "pg_db"

    @property
    def ASYNC_DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"  # noqa: WPS221, E501


class ProfileApi(BaseModel):
    host: str = "localhost"
    port: int = 8000
    auth_header: str = "x-api-key"
    api_key: str = "9333954892f3ce159e33c829af5ea4b93cc2385306b45158ca95bc31f195c943"
    profile_path: str = "/auth/api/v1/internal/fetch-profiles"

    @property
    def get_profile_url(self) -> str:
        return f"http://{self.host}:{self.port}{self.profile_path}"


class AppConfig(BaseSettings):
    tracing: bool = False
    project_name: str = "notification-service"
    docs_url: str = "/notification/openapi"
    openapi_url: str = "/notification/openapi.json"
    single_notify_batch: int = 10

    notify_start_hour: int = 9
    notify_end_hour: int = 20

    server: Server = Server()
    postgres: Postgres = Postgres()
    profile_api: ProfileApi = ProfileApi()

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        case_sensitive=False,
        env_nested_delimiter="_",
        extra="ignore",
    )


def _get_config() -> AppConfig:
    log = LoggerSettings()
    log.apply()
    logger = logging.getLogger(__name__)
    app_config = AppConfig()
    logger.info(f"app_config.initialized: {app_config.model_dump_json(indent=4)}")
    return app_config


app_config = _get_config()
