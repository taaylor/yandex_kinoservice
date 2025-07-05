import asyncio
import logging
import random
from functools import wraps
from typing import Any, Callable, Coroutine, Type

from fastapi import HTTPException, status
from sqlalchemy.exc import (
    DBAPIError,
    DisconnectionError,
    IntegrityError,
    InterfaceError,
    MultipleResultsFound,
    NoResultFound,
    OperationalError,
)
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def backoff[**P, R](  # noqa: WPS211, WPS231, WPS234
    exception: tuple[Type[Exception], ...],
    start_sleep_time: float = 0.1,
    factor: float = 2,
    border_sleep_time: float = 10,
    jitter: bool = True,
    max_attempts: int = 5,
) -> Callable[
    [Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]  # noqa: WPS221
]:
    def func_wrapper(  # noqa: WPS430, WPS231
        func: Callable[P, Coroutine[Any, Any, R]],
    ) -> Callable[P, Coroutine[Any, Any, R]]:  # noqa: WPS221
        @wraps(func)
        async def wrapper(  # noqa: WPS231
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> R:
            time = start_sleep_time
            attempt = 1
            last_exception = None
            session: AsyncSession = kwargs.get("session")  # type: ignore

            if not session and len(args) >= 2:
                session = args[1]

            while attempt <= max_attempts:
                try:
                    return await func(*args, **kwargs)  # type: ignore
                except exception as error:
                    await session.rollback()
                    last_exception = error
                    logger.error(
                        f"Возникло исключение: {error}. Попытка {attempt}/{max_attempts}",
                    )
                except Exception as error:
                    await session.rollback()
                    last_exception = error
                    logger.error(
                        f"Возникло исключение: {error}. Попытка {attempt}/{max_attempts}",
                    )

                if attempt == max_attempts:
                    logger.error("Backoff исчерпал попытки, прокидываю исключение...")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Ошибка стороннего сервиса, повторите попытку позже",
                    ) from last_exception

                if jitter:
                    time += random.uniform(0, time * 0.1)
                await asyncio.sleep(time)
                time = min(time * factor, border_sleep_time)
                attempt += 1

            raise RuntimeError("Неожиданная ошибка в backoff")

        return wrapper

    return func_wrapper


def sqlalchemy_handler_400_exceptions[**P, R](  # noqa: WPS231, WPS114
    func: Callable[P, Coroutine[Any, Any, R]],
) -> Callable[P, Coroutine[Any, Any, R | None]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        session: AsyncSession = kwargs.get("session")  # type: ignore
        if not session and len(args) >= 2:
            session = args[1]

        try:
            return await func(*args, **kwargs)
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Нарушение целостности данных: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нарушение уникальности",
            )

        except NoResultFound as e:
            await session.rollback()
            logger.warning(f"Запись не найдена: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Запись не найдена",
            )

        except MultipleResultsFound as e:
            await session.rollback()
            logger.error(f"Найдено несколько записей: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка: найдено несколько записей",
            )

    return wrapper


def sqlalchemy_universal_decorator[**P, R](
    func: Callable[P, Coroutine[Any, Any, R]],
) -> Callable[P, Coroutine[Any, Any, R | None]]:
    @backoff(
        exception=(DBAPIError, DisconnectionError, InterfaceError, OperationalError),
        max_attempts=5,
    )
    @sqlalchemy_handler_400_exceptions
    @wraps(func)
    async def wrapper(*args, **kwargs) -> R:
        session: AsyncSession = kwargs.get("session")  # type: ignore
        if not session and len(args) >= 2:
            session = args[1]

        if session is None:
            raise ValueError("Сессия должна быть передана в функцию")

        result = await func(*args, **kwargs)  # type: ignore
        await session.commit()
        return result

    return wrapper
