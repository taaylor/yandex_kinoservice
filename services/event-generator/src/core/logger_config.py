import logging
from logging import config as logging_config
from typing import Any

import dotenv
from opentelemetry import context as context_api
from opentelemetry.baggage import get_baggage
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = dotenv.find_dotenv()


factory = logging.getLogRecordFactory()


def record_factory(*args, **kwargs):
    record = factory(*args, **kwargs)
    context = context_api.get_current()
    record.request_id = get_baggage("request_id", context) or "N/A"
    return record


logging.setLogRecordFactory(record_factory)


class LoggerSettings(BaseSettings):
    log_level: str = "DEBUG"
    log_format: str = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s - request_id: %(request_id)s"
    )
    log_default_handlers: list[str] = [
        "console",
    ]
    logger_config: dict[str, Any] = {}

    model_config = SettingsConfigDict(env_prefix="LOG_", env_file=ENV_FILE, extra="ignore")

    @model_validator(mode="after")
    def init_loggind(self) -> "LoggerSettings":
        self.logger_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "verbose": {"format": self.log_format},
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(levelprefix)s %(message)s",
                    "use_colors": None,
                },
                "access": {
                    "()": "uvicorn.logging.AccessFormatter",
                    "fmt": "%(levelprefix)s %(client_addr)s - '%(request_line)s' %(status_code)s",
                },
            },
            "handlers": {
                "console": {
                    "level": self.log_level,
                    "class": "logging.StreamHandler",
                    "formatter": "verbose",
                },
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
                "access": {
                    "formatter": "access",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "": {
                    "handlers": self.log_default_handlers,
                    "level": self.log_level,
                },
                "uvicorn.error": {
                    "level": self.log_level,
                },
                "uvicorn.access": {
                    "handlers": ["access"],
                    "level": self.log_level,
                    "propagate": False,
                },
                # Настройки для PyMongo логгеров
                "pymongo": {
                    "level": "ERROR",
                    "handlers": self.log_default_handlers,
                    "propagate": False,
                },
                "pymongo.connection": {
                    "level": "ERROR",
                    "handlers": self.log_default_handlers,
                    "propagate": False,
                },
                "pymongo.command": {
                    "level": "ERROR",
                    "handlers": self.log_default_handlers,
                    "propagate": False,
                },
            },
            "root": {
                "level": self.log_level,
                "formatter": "verbose",
                "handlers": self.log_default_handlers,
            },
        }
        return self

    def apply(self) -> None:
        """Применить настройки логирования один раз при старте приложения."""
        logging_config.dictConfig(self.logger_config)
