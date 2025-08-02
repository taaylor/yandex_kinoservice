import abc
from typing import Any


class DBAbstract(abc.ABC):

    @classmethod
    @abc.abstractmethod
    async def close(cls) -> None:
        """Закрывает соединение с БД"""

    @abc.abstractmethod
    async def fetch(self, query: str, *args, **kwargs) -> Any:
        """Метод делает запрос в БД, и возвращает результат"""
