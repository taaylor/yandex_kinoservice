import base64
import binascii
from http import HTTPStatus

import numpy as np
import pytest
from tests.functional.core.settings import test_conf


@pytest.mark.asyncio
class TestEmbeddings:

    @staticmethod
    def is_base64(s: str) -> bool:
        try:
            decoded = base64.b64decode(s, validate=True)
            return len(decoded) > 0
        except (binascii.Error, ValueError):
            return False

    @staticmethod
    def decode_b64(s: str) -> list[float]:
        embedding_bytes = base64.b64decode(s)
        embedding_f32 = np.frombuffer(embedding_bytes, dtype=np.float32)
        embedding_f64 = [float(v) for v in embedding_f32]
        return embedding_f64

    @pytest.mark.parametrize(
        "payload_data, expected_answer",
        [
            (
                {},
                {
                    "status": HTTPStatus.BAD_REQUEST,
                    "err_msg": (
                        "Для пустого objects статус код" f" должен быть {HTTPStatus.BAD_REQUEST}"
                    ),
                },
            ),
            (
                {
                    "objects": [],
                },
                {
                    "status": HTTPStatus.BAD_REQUEST,
                    "err_msg": (
                        "Для пустого objects статус код" f" должен быть {HTTPStatus.BAD_REQUEST}"
                    ),
                },
            ),
            (
                {
                    "objects": [{"text": "test-text"}],
                },
                {
                    "status": HTTPStatus.BAD_REQUEST,
                    "err_msg": (
                        "Для отсутствующего id статус код" f" должен быть {HTTPStatus.BAD_REQUEST}"
                    ),
                },
            ),
            (
                {
                    "objects": [{"id": "123"}],
                },
                {
                    "status": HTTPStatus.BAD_REQUEST,
                    "err_msg": (
                        "Для отсутствующего text статус код"
                        f" должен быть {HTTPStatus.BAD_REQUEST}"
                    ),
                },
            ),
        ],
        ids=[
            "Test empty payload",
            "Test empty objects",
            "Test absent id",
            "Test absent text",
        ],
    )
    async def test_invalid_queries(
        self,
        make_post_request,
        payload_data: dict[str, list[float]],
        expected_answer: dict[str, list[str]],
    ):
        body, status = await make_post_request(
            url=test_conf.embeddingapi.url_for_embedding,
            data=payload_data,
        )
        assert status == expected_answer["status"], expected_answer["err_msg"]

    @pytest.mark.parametrize(
        "payload_data, expected_answer",
        [
            (
                {"objects": [{"id": "123", "text": "test-text"}]},
                {
                    "status": HTTPStatus.OK,
                    "embedding_dims": test_conf.embeddingapi.embedding_dims,
                    "payload_length": 1,
                    "err_msg_status_code": f"Cтатус код должен быть {HTTPStatus.OK}",
                    "err_msg_valid_b64": "Строка невалидна для base64",
                    "err_msg_wrong_len_payload": "Вернулся пустой список",
                    "err_msg_wrong_len_vector": (
                        "Размерность вектора отличается от"
                        f" {test_conf.embeddingapi.embedding_dims}"
                    ),
                },
            ),
        ],
        ids=[
            "Test one text",
        ],
    )
    async def test_one_text(
        self,
        make_post_request,
        payload_data: dict[str, list[float]],
        expected_answer: dict[str, list[str]],
    ):
        body, status = await make_post_request(
            url=test_conf.embeddingapi.url_for_embedding,
            data=payload_data,
        )

        # сравниваем статус код
        assert status == expected_answer["status"], expected_answer["err_msg_status_code"]

        # сравниваем длину ответа
        assert len(body) == expected_answer["payload_length"], expected_answer[
            "err_msg_wrong_len_payload"
        ]

        embedding = body[0]["embedding"]

        # сравниваем что строка валидна для base64
        assert self.is_base64(embedding), expected_answer["err_msg_valid_b64"]

        # сравниваем то что размерность вектора действительно 384
        assert (
            len(self.decode_b64(embedding)) == expected_answer["embedding_dims"]
        ), expected_answer["err_msg_wrong_len_vector"]

    @pytest.mark.parametrize(
        "payload_data, expected_answer",
        [
            (
                {
                    "objects": [
                        {"id": "123", "text": "test-text-1"},
                        {"id": "123", "text": "test-text-2"},
                        {"id": "123", "text": "test-text-3"},
                    ]
                },
                {
                    "status": HTTPStatus.OK,
                    "embedding_dims": test_conf.embeddingapi.embedding_dims,
                    "err_msg_status_code": f"Cтатус код должен быть {HTTPStatus.OK}",
                    "payload_length": 3,
                    "err_msg_valid_b64": "Строка невалидна для base64",
                    "err_msg_wrong_len_payload": "Вернулся пустой список",
                    "err_msg_wrong_len_vector": (
                        "Размерность вектора отличается от"
                        f" {test_conf.embeddingapi.embedding_dims}"
                    ),
                },
            ),
        ],
        ids=[
            "Test many texts",
        ],
    )
    async def test_many_texts(
        self,
        make_post_request,
        payload_data: dict[str, list[float]],
        expected_answer: dict[str, list[str]],
    ):
        body, status = await make_post_request(
            url=test_conf.embeddingapi.url_for_embedding,
            data=payload_data,
        )

        # сравниваем статус код
        assert status == expected_answer["status"], expected_answer["err_msg_status_code"]

        # сравниваем длину ответа
        assert len(body) == expected_answer["payload_length"], expected_answer[
            "err_msg_wrong_len_payload"
        ]

        embedding_ls = [item["embedding"] for item in body]

        # сравниваем что строка валидна для base64
        for embedding in embedding_ls:
            assert self.is_base64(embedding), expected_answer["err_msg_valid_b64"]

            # сравниваем то что размерность вектора действительно 384
            assert (
                len(self.decode_b64(embedding)) == expected_answer["embedding_dims"]
            ), expected_answer["err_msg_wrong_len_vector"]
