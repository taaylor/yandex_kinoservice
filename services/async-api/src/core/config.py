import dotenv
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


class RecProfileSupplier(BaseModel):
    host: str = "localhost"
    port: int = 8005
    timeout: int = 30

    @property
    def get_url(self) -> str:
        return f"http://{self.host}:{self.port}/recs-profile/api/v1/recs/fetch-user-recs"


class StatisticSupplier(BaseModel):
    host: str = "localhost"
    port: int = 8010
    timeout: int = 30

    @property
    def get_url(self) -> str:
        return f"http://{self.host}:{self.port}/statistic/api/v1/trends/fetch-trends-films"


class AppConfig(BaseSettings):
    project_name: str = "async-service"
    docs_url: str = "/async/openapi"
    openapi_url: str = "/async/openapi.json"
    cache_expire_in_seconds: int = 300
    tracing: bool = False
    embedding_dims: int = 384

    elastic: Elastic = Elastic()
    redis: Redis = Redis()
    server: Server = Server()
    rec_profile_supplier: RecProfileSupplier = RecProfileSupplier()
    statistic_supplier: StatisticSupplier = StatisticSupplier()

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        case_sensitive=False,
        env_nested_delimiter="_",
        extra="ignore",
    )


def _get_config() -> AppConfig:
    import logging

    from core.logger_config import LoggerSettings

    LoggerSettings().apply()
    logger = logging.getLogger(__name__)

    app_config = AppConfig()
    logger.info(f"app_config.initialized: {app_config.model_dump_json(indent=4)}")
    return app_config


app_config = _get_config()
