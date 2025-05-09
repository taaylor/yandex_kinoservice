import logging

import dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = dotenv.find_dotenv()

logger = logging.getLogger(__name__)

logger.info(f"ENV АВТОРИЗАЦИЯ: {ENV_FILE}")


class Jaeger(BaseModel):
    host: str = "localhost"
    port: str = "4317"

    @property
    def jaeger_url(self):
        return f"http://{self.host}:{self.port}"


class TracerUtilsConfig(BaseSettings):
    trace_percent: float = 1.0

    jaeger: Jaeger = Jaeger()

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        case_sensitive=False,
        env_nested_delimiter="_",
        extra="ignore",
    )


def _get_config() -> TracerUtilsConfig:
    app_config = TracerUtilsConfig()
    logger.info(f"tracer_utils_conf.initialized: {app_config.model_dump_json(indent=4)}")
    return app_config


tracer_conf = _get_config()
