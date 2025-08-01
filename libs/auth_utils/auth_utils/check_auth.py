import logging
from typing import Annotated
from uuid import UUID

import backoff
from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer
from fastapi import Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from redis.asyncio import Redis
from redis.exceptions import RedisError

from .auth_utils_config import auth_utils_conf

logger = logging.getLogger(__name__)

CACHE_KEY_DROP_SESSION = auth_utils_conf.cache_key_drop_session


redis_conn = Redis(
    host=auth_utils_conf.redis.host,
    port=auth_utils_conf.redis.port,
    username=auth_utils_conf.redis.user,
    password=auth_utils_conf.redis.password,
    db=auth_utils_conf.redis.db,
)


class JWTSettings(BaseModel):
    authjwt_algorithm: str = auth_utils_conf.algorithm
    authjwt_public_key: str = auth_utils_conf.public_key
    authjwt_denylist_enabled: bool = auth_utils_conf.denylist_enabled
    authjwt_denylist_token_checks: set = auth_utils_conf.token_checks


# Кастомный класс, чтобы не было конфликтов с обычным AuthJWT
class LibAuthJWT(AuthJWT):
    """Изолированная версия AuthJWT для библиотеки"""

    async def compare_permissions(
        self,
        decrypted_token: dict,
        required_permissions: set,
    ) -> set[str]:
        user_permissions = set(decrypted_token["permissions"])

        logger.info(
            f"Из токена пользователя:{decrypted_token.get('user_id')}, с ролью: {decrypted_token.get('role_code')} получены разрешения {user_permissions}",  # noqa: E501
        )

        result = required_permissions.issubset(user_permissions)
        logger.info(
            f"Сравнение разрешений пользователя: {user_permissions} и необходимых разрешений: {required_permissions}. Результат: {result}",  # noqa: E501
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для выполнения действия",
            )

        return user_permissions


# Кастомный класс, чтобы не было конфликтов с обычным AuthJWT
class LibAuthJWTBearer(AuthJWTBearer):
    """Bearer с изолированной конфигурацией"""

    def __call__(self, req: Request = None, res: Response = None) -> LibAuthJWT:  # type: ignore
        return LibAuthJWT(req=req, res=res)  # Возвращаем экземпляр кастомного класса


@LibAuthJWT.load_config  # type: ignore
def get_config() -> JWTSettings:
    settings = JWTSettings()
    logger.info(f"Конфигурация JWT библиотеки: {settings.model_dump_json(indent=4)}")
    return settings


@AuthJWT.token_in_denylist_loader  # type: ignore
@backoff.on_exception(
    backoff.expo,
    (RedisError, ConnectionError),
    max_tries=5,
    jitter=backoff.full_jitter,
)
async def check_if_session_in_denylist(decrypted_token: dict) -> bool:
    logger.info(f"Проверка токена: {decrypted_token}")
    user_id = decrypted_token.get("user_id")
    session_id = decrypted_token.get("session_id")

    cache_key = CACHE_KEY_DROP_SESSION.format(user_id=user_id, session_id=session_id)
    try:
        entry = await redis_conn.get(cache_key)
        return entry is not None
    except (RedisError, ConnectionError) as e:
        logger.error(f"Ошибка при обращении к Redis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при проверке токена в denylist",
        )


auth_dep = LibAuthJWTBearer()


# Вынесенная зависимость для проверки JWT и извлечения user_id
async def get_current_user_id(authorize: Annotated[LibAuthJWT, Depends(auth_dep)]) -> UUID:
    await authorize.jwt_required()
    user_jwt_id = UUID((await authorize.get_raw_jwt())["user_id"])  # type: ignore
    return user_jwt_id
