import logging
from enum import StrEnum

import dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = dotenv.find_dotenv()

logger = logging.getLogger(__name__)

logger.info(f"ENV АВТОРИЗАЦИЯ: {ENV_FILE}")


class Permissions(StrEnum):
    CRUD_ROLE = "CRUD_ROLE"
    CRUD_FILMS = "CRUD_FILMS"
    FREE_FILMS = "FREE_FILMS"
    PAID_FILMS = "PAID_FILMS"
    ASSIGN_ROLE = "ASSIGN_ROLE"


class Redis(BaseModel):
    host: str = "localhost"
    port: int = 6379
    user: str = "redis_user"
    password: str = "Parol123"
    db: int = 0


class AuthUtilsConfig(BaseSettings):
    algorithm: str = "RS256"
    cache_key_drop_session: str = "session:drop:{user_id}:{session_id}"
    denylist_enabled: bool = True
    token_checks: set = {"access", "refresh"}
    public_key: str = """
    -----BEGIN PUBLIC KEY-----
    MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArW7XpysaZje95xChyW8u
    L8xGDbvUezcygQNcYep97eM9Vurhk+5BSgNF5sQfW/IeMCH2EtbQi+tVuyTYcelG
    Gs2Flln/AHXdE6UqiS3AKvRxuvZTWetf80AGcyl7Sax2SY+j6sPSwy/q+SpaxYMf
    QOx0buewylTZ7MUkkepsDf7ZbYZfzyUOUUzGilDWeKskKNt9ujCdZYNy6+37xWru
    LsIdrTFC1/ggReddwEM4/VNvK5q+go+SCDfVgfQ8LbMiCgkKyZ3fgeP+KFsbCL/d
    iaqd0feQZY8tFMEttcBzQaZUny2pjJ+cBNmkRJG54vD1wl3ujSIfimJ2gQTmCPvf
    iwIDAQAB
    -----END PUBLIC KEY-----
    """

    redis: Redis = Redis()

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        case_sensitive=False,
        env_nested_delimiter="_",
        extra="ignore",
    )


def _get_config() -> AuthUtilsConfig:
    app_config = AuthUtilsConfig()
    logger.info(f"auth_utils_conf.initialized: {app_config.model_dump_json(indent=4)}")
    return app_config


auth_utils_conf = _get_config()
