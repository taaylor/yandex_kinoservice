import base64
import logging
from uuid import UUID

import backoff
import httpx
import numpy as np
from core.config import app_config
from models.logic_models import QueryModel
from suppliers.base_supplier import BaseSupplier
from utils.http_decorators import EmptyServerResponse, handle_http_errors

logger = logging.getLogger(__name__)


class EmbeddingSupplier(BaseSupplier):

    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, httpx.HTTPStatusError),
        max_tries=3,
        jitter=backoff.full_jitter,
    )
    @handle_http_errors(service_name=app_config.filmapi.host)
    async def fetch_embedding(
        self, texts: list[QueryModel]
    ) -> dict[UUID, list[float]]:  # noqa: WPS210
        """Отправляет запрос на получение эмбеддинга для заданного текста."""

        async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as client:
            data = {"objects": [t.model_dump(mode="json") for t in texts]}
            url = app_config.embedding_api.get_url

            logger.debug(f"Сформирована строка запроса: {url}")
            logger.debug(f"Сформирована data запроса: {data}")

            response = await client.post(url=url, json=data)
            response.raise_for_status()
            if not response.content:
                logger.error(f"Пустой ответ от сервиса {app_config.embedding_api.host}")
                raise EmptyServerResponse(
                    f"Получен пустой ответ от {app_config.embedding_api.host}"
                )
            embedding_response = response.json()
            logger.info(f"Получен ответ на запрос эмбеддинга: {embedding_response}")

            return self._decode_embedding(embedding_response)

    def _decode_embedding(
        self, embedding_response: list[dict[str, str]]
    ) -> dict[UUID, list[float]]:
        """Декодирует эмбеддинг из ответа сервиса."""
        embeddings = {}

        # Example response: {"id": "1234", "embedding": "<base64_string>"}
        for embedding in embedding_response:
            embedding_id = UUID(embedding["id"])
            embedding_base64 = embedding["embedding"]
            embedding_bytes = base64.b64decode(embedding_base64)
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
            embeddings[embedding_id] = [float(v) for v in embedding]
        return embeddings


def get_embedding_supplier() -> EmbeddingSupplier:
    """Возвращает экземпляр поставщика эмбеддингов."""
    return EmbeddingSupplier()
