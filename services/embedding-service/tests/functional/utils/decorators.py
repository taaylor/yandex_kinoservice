import logging
import random
import time
from functools import wraps
from typing import Any, Callable, Type

logger = logging.getLogger(__name__)


def backoff(
    exception: tuple[Type[Exception], ...],
    start_sleep_time: float = 0.1,
    factor: float = 2,
    border_sleep_time: float = 10,
    jitter: bool = True,
    max_attempts: int = 5,
):
    def func_wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            sleep_time = start_sleep_time
            attempt = 1
            last_exception = None

            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exception as error:
                    last_exception = error
                    logger.error(
                        f"Возникло исключение: {error}. Попытка {attempt}/{max_attempts}",
                    )
                except Exception as error:
                    last_exception = error
                    logger.error(
                        f"Возникло исключение: {error}. Попытка {attempt}/{max_attempts}",
                    )
                if jitter:
                    sleep_time += random.uniform(0, sleep_time * 0.1)
                time.sleep(sleep_time)
                sleep_time = min(sleep_time * factor, border_sleep_time)
                attempt += 1
            logger.error("Backoff исчерпал попытки, прокидываю исключение...")
            err_output = f"Функция {func.__name__} не выполнилась" f" после {max_attempts} попыток."
            raise RuntimeError(err_output) from last_exception

        return wrapper

    return func_wrapper
