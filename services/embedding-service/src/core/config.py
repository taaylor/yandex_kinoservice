from dotenv import find_dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = find_dotenv()


class Server(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    timeout: int = 30
    backlog: int = 512
    max_requests: int = 1000
    max_requests_jitter: int = 50
    worker_class: str = "uvicorn.workers.UvicornWorker"


class AppConfig(BaseSettings):
    debug: bool = True
    project_name: str = "embedding-service"
    docs_url: str = "/embedding-service/openapi"
    openapi_url: str = "/embedding-service/openapi.json"

    server: Server = Server()

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        case_sensitive=False,
        env_nested_delimiter="_",
        extra="ignore",
    )


def _get_app_config() -> AppConfig:

    import logging

    from core.logger_conf import LoggerSettings

    LoggerSettings().apply()

    logger = logging.getLogger(__name__)
    config = AppConfig()
    logger.info(f"Инициализация конфигурации: {config.model_dump_json(indent=4)}")

    return config


app_config = _get_app_config()
