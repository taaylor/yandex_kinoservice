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


class Postgres(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    db: str = "pg_db"

    @property
    def ASYNC_DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    @property
    def SYNC_DATABASE_URL(self):
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class Redis(BaseModel):
    host: str = "localhost"
    port: int = 6379
    user: str = "redis_user"
    password: str = "Parol123"
    db: int = 0


class JWTSettings(BaseModel):
    private_key_path: str = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "keys/private.pem"
    )
    public_key_path: str = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "keys/public.pem"
    )
    algorithm: str = "RS256"
    access_token_lifetime_sec: int = 1200  # 10 минут
    refresh_token_lifetime_sec: int = 2400  # 40 минут
    cache_key_drop_session: str = "session:drop:{user_id}:{session_id}"


class AppConfig(BaseSettings):
    project_name: str = "auth-service"
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_url: str = "/auth/openapi"
    openapi_url: str = "/auth/openapi.json"
    cache_expire_in_seconds: int = 300  # время кэширование ответа (сек.)
    default_role: str = "UNSUB_USER"
    tracing: bool = False  # включение/выключение трассировки

    postgres: Postgres = Postgres()
    redis: Redis = Redis()
    server: Server = Server()
    jwt: JWTSettings = JWTSettings()

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
