from logging import config as logging_config
from typing import Any

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggerSettings(BaseSettings):
    log_level: str = "DEBUG"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_default_handlers: list[str] = ["console"]
    logger_config: dict[str, Any] = {}

    model_config = SettingsConfigDict(env_prefix="LOG_", extra="ignore")

    @model_validator(mode="after")
    def init_logging(self) -> "LoggerSettings":
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
            },
        }
        return self

    def apply(self) -> None:
        """Применить настройки логирования"""
        logging_config.dictConfig(self.logger_config)
