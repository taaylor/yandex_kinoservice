from dotenv import find_dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Server(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080
    timeout: int = 30
    backlog: int = 512
    max_requests: int = 1000
    max_requests_jitter: int = 50
    worker_class: str = "aiohttp.GunicornWebWorker"


class RabbitMQ(BaseModel):
    hosts: list[str] = ["rabbitmq-1", "rabbitmq-3", "rabbitmq-3"]
    user: str = "user"
    password: str = "pass"
    review_like_queue: str = "user-review.liked.natification-api.websocket-sender"


class Redis(BaseModel):
    host: str = "localhost"
    port: int = 6379
    user: str = "redis_user"
    password: str = "Parol123"
    db: int = 0


class Config(BaseSettings):
    rabbitmq: RabbitMQ = RabbitMQ()
    redis: Redis = Redis()
    server: Server = Server()

    model_config = SettingsConfigDict(
        env_file=find_dotenv(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="_",
        extra="ignore",
    )


def get_config() -> Config:
    import logging

    from core.logger_conf import LoggerSettings

    logger_settings = LoggerSettings()
    logger_settings.apply()
    logger = logging.getLogger(__name__)

    config = Config()
    logger.debug(f"Инициализация конфигурации: {config.model_dump_json(indent=4)}")
    return config


app_config = get_config()
