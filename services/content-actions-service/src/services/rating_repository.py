import logging
from functools import lru_cache
from typing import Any

from models.logic_models import AvgRatingSchema
from models.models import Rating
from services.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class RatingRepository(BaseRepository[Rating]):
    """Репозиторий для работы с рейтингами (модель Rating)."""

    __slots__ = ("collection",)  # переопределяем в классе наследнике, т.к. __slots__ не наследуется

    async def calculate_average_rating(self, *filters: Any) -> list[AvgRatingSchema] | None:
        """
        Вычисляет среднюю оценку и количество голосов по указанным фильтрам.

        :param filters: Условия фильтрации, например Rating.film_id == film_id.
        :return: Список объектов `AvgRatingSchema`, каждый содержащий:
                 - film_id (_id из агрегации)
                 - avg_rating (среднее арифметическое)
                 - votes_count (число голосов);
                 или None, если по фильтрам нет документов.
        """
        document = (
            await self.collection.find(*filters)
            .aggregate(
                [
                    {
                        "$group": {
                            "_id": "$film_id",
                            "avg_rating": {"$avg": "$score"},
                            "votes_count": {"$sum": 1},
                        }
                    }
                ],
                projection_model=AvgRatingSchema,
            )
            .to_list()
        )
        if not document:
            logger.debug(f"Документ по фильтрам {filters} не найден")
            return None
        logger.debug(f"Документ по фильтрам {filters} найден")
        return document


@lru_cache()
def get_rating_repository() -> RatingRepository:
    return RatingRepository(Rating)
