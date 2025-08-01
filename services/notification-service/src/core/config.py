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
    profile_all_path: str = "/auth/api/v1/internal/fetch-all-profiles"

    @property
    def get_profile_url(self) -> str:
        return f"http://{self.host}:{self.port}{self.profile_path}"

    @property
    def get_all_profiles_url(self) -> str:
        return f"http://{self.host}:{self.port}{self.profile_all_path}"


class FilmApi(BaseModel):
    host: str = "localhost"
    port: int = 8001
    film_path: str = "/async/api/v1/internal/fetch-films"

    @property
    def get_film_url(self) -> str:
        return f"http://{self.host}:{self.port}{self.film_path}"


class Redis(BaseModel):
    host: str = "localhost"
    port: int = 6379
    user: str = "redis_user"
    password: str = "Parol123"
    db: int = 0


class RabbitMQ(BaseModel):
    review_like_queue: str = "user-review.liked.notification.websocket-sender"
    registered_queue: str = "user.registered.notification.email-sender"
    manager_mailing_queue: str = "manager-mailing.launched.notification.email-sender"
    auto_mailing_queue: str = "auto-mailing.launched.notification.email-sender"

    host1: str = "localhost"
    host2: str = "localhost"
    host3: str = "localhost"
    port: int = 5672

    user: str = "user"
    password: str = "pass"

    def get_host(self, host_number: int = 1) -> str:
        if host_number == 2:
            return f"amqp://{self.user}:{self.password}@{self.host2}:{self.port}/"
        elif host_number == 3:
            return f"amqp://{self.user}:{self.password}@{self.host3}:{self.port}/"
        return f"amqp://{self.user}:{self.password}@{self.host1}:{self.port}/"


class AppConfig(BaseSettings):
    tracing: bool = False
    project_name: str = "notification-service"
    docs_url: str = "/notification/openapi"
    openapi_url: str = "/notification/openapi.json"
    single_notify_batch: int = 10
    mass_notify_batch: int = 5
    profile_page_size: int = 50
    expire_cache_sec: int = 3600

    start_processing_interval_sec: int = 10
    notify_start_hour: int = 9
    notify_end_hour: int = 20

    server: Server = Server()
    postgres: Postgres = Postgres()
    profileapi: ProfileApi = ProfileApi()
    filmapi: FilmApi = FilmApi()
    rabbitmq: RabbitMQ = RabbitMQ()
    redis: Redis = Redis()

    templates: dict[str, str] = {"user_registered_type": "f69248f5-4f6c-4cd4-82ca-e8f6cd68483f"}

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
