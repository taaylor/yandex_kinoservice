import logging.config
from typing import Any

import dotenv
from pydantic import ConfigDict, model_validator
from pydantic_settings import BaseSettings

ENV_FILE = dotenv.find_dotenv()


class LoggerSettings(BaseSettings):
    log_level: str = "DEBUG"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_default_handlers: list[str] = [
        "console",
    ]
    logging: dict[str, Any] = {}

    model_config = ConfigDict(env_prefix="LOG_", env_file=ENV_FILE, extra="ignore")

    @model_validator(mode="after")
    def init_loggind(self) -> "LoggerSettings":
        self.logging = {
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
            "root": {
                "level": self.log_level,
                "formatter": "verbose",
                "handlers": self.log_default_handlers,
            },
        }
        return self

    def apply(self) -> None:
        """Применить настройки логирования один раз при старте приложения."""
        logging.config.dictConfig(self.logging)
