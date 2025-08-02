import logging
from functools import lru_cache
from http import HTTPMethod
from typing import Any
from uuid import UUID

from core.config import app_config
from suppliers.base_supplier import BaseSupplier

logger = logging.getLogger(__name__)


class RecProfileSupplier(BaseSupplier):

    async def fetch_rec_profile_user(self, user_id: UUID) -> list[list[float]] | None:
        url = app_config.rec_profile_supplier.get_url
        user_id_str = str(user_id)
        body = {
            "user_ids": [
                user_id_str,
            ]
        }
        rec_profile = await self._make_request(HTTPMethod.POST, url, body)
        if rec_profile:
            rec_profile_dto = self._parser_embeddings(rec_profile.get("recs", {}))
            return rec_profile_dto.get(user_id_str)
        return None

    @staticmethod
    def _parser_embeddings(rec_profiles: list[dict[str, Any]]) -> dict[str, list[list[float]]]:
        embeddings = {}
        validate_func = lambda x: isinstance(x, float)  # noqa: E731

        for user in rec_profiles:
            user_id = user.get("user_id")
            for embedding in user.get("embeddings", []):
                emb = embedding.get("embedding", [])

                if (
                    emb
                    and len(emb) == app_config.embedding_dims
                    and all(validate_func(e) for e in emb)
                ):
                    if user_id not in embedding:
                        embeddings[user_id] = []
                    embeddings[user_id].append(emb)

        logger.info(f"Получены вектора для {len(embeddings)} пользователей")
        return embeddings


@lru_cache
def get_rec_profile_supplier() -> RecProfileSupplier:
    return RecProfileSupplier(
        service_name="recs-profile-service", timeout=app_config.rec_profile_supplier.timeout
    )
