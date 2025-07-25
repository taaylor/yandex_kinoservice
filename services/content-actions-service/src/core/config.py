import logging
import os
from collections.abc import Sequence
from typing import Type
from uuid import UUID

import dotenv
from core.logger_config import LoggerSettings
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pymongo.errors import ConnectionFailure, NetworkTimeout, PyMongoError

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


class MongoDB(BaseModel):
    host: str = "localhost"
    port: int = 27017
    name: str = "kinoservice"
    like_coll: str = "likeCollection"
    bookmark_coll: str = "bookmarkCollection"
    reviews_coll: str = "reviewsCollection"
    reviews_like_coll: str = "reviewslikeCollection"
    base_connect_exp: Sequence[Type[Exception]] = Field(
        (ConnectionFailure, NetworkTimeout, PyMongoError), exclude=True
    )

    @property
    def ASYNC_DATABASE_URL(self):
        return f"mongodb://{self.host}:{self.port}"


class NotificationAPI(BaseModel):
    host: str = "localhost"
    port: int = 8001
    profile_path: str = "/notification/api/v1/notifications/single-notification"
    timeout_sec: int = 30

    @property
    def get_notify_url(self) -> str:
        return f"http://{self.host}:{self.port}{self.profile_path}"


class Kafka(BaseModel):
    host1: str = "localhost"
    port1: int = 9094
    host2: str = "localhost"
    port2: int = 9095
    host3: str = "localhost"
    port3: int = 9096

    retry_backoff_ms: int = 100
    request_timeout_ms: int = 5000
    batch_size: int = 5120
    linger_ms: int = 5
    buffer_memory: int = 33554432
    security_protocol: str = "PLAINTEXT"

    @property
    def get_servers(self) -> list[str]:
        return [
            f"{self.host1}:{self.port1}",
            f"{self.host2}:{self.port2}",
            f"{self.host3}:{self.port3}",
        ]

    rec_bookmarks_list_topic: str = "rec_bookmarks_list_topic"
    rec_user_ratings_films_topic: str = "rec_user_ratings_films_topic"


class AppConfig(BaseSettings):
    glitchtip_url: str = "url"
    is_glitchtip_enabled: bool = False
    project_name: str = "content-actions-service"
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # noqa: WPS221
    docs_url: str = "/content-api/openapi"
    openapi_url: str = "/content-api/openapi.json"
    tracing: bool = False  # включение/выключение трассировки
    cache_expire_in_seconds: int = 300  # время кэширование ответа (сек.)
    default_http_timeout: float = 3.0
    film_validation_url: str = "http://localhost/async/api/v1/films/{film_id}"
    max_page_size: int = 50
    min_page_size: int = 1

    test_films: set[UUID] = {
        UUID("3e5351d6-4e4a-486b-8529-977672177a07"),
        UUID("a88cbbeb-b998-4ca6-aeff-501463dcdaa0"),
        UUID("7f28af8a-c629-4af0-b87b-39368a5b8464"),
        UUID("ee1baa06-a221-4d8c-8678-992e8e84c5c1"),
        UUID("e5a21648-59b1-4672-ac3b-867bcd64b6ea"),
        UUID("f061235e-779f-4a59-9eaa-fc533c3c0584"),
        UUID("b16d59f7-a386-467b-bea3-35e7ffbba902"),
        UUID("53d660a1-be2b-4b53-9761-0a315a693789"),
        UUID("0312ed51-8833-413f-bff5-0e139c11264a"),
        UUID("991d143e-1342-4f7c-abf0-a9ede3abba20"),
        UUID("248041f8-8c65-4539-b684-e8f4cd01d10f"),
        UUID("db594b91-a587-48c4-bac9-5c6be5e4cf33"),
        UUID("f553752e-71c7-4ea0-b780-41408516d0f4"),
        UUID("00e2e781-7af9-4f82-b4e9-14a488a3e184"),
        UUID("aa5aea7a-cd65-4aec-963f-98375b370717"),
    }

    redis: Redis = Redis()
    mongodb: MongoDB = MongoDB()  # type: ignore
    server: Server = Server()
    notification_api: NotificationAPI = NotificationAPI()
    kafka: Kafka = Kafka()

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
