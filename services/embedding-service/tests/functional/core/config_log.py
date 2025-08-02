import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """Функция для создания и настройки логгера.

    :param name: Имя логгера.
    Возвращаяет настроенный logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.hasHandlers():
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger
