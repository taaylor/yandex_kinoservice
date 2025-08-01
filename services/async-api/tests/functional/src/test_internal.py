import random
from http import HTTPStatus

import pytest
from tests.functional.core.settings import test_conf
from tests.functional.testdata.es_mapping import Mapping


@pytest.mark.asyncio
class TestFilmsSearchByVector:

    def prepare_uuids_and_vectors(self):
        film_uuids_for_near_embedding = [
            "3d825f60-9fff-4dfe-b294-1a45fa1e115d",
            "0312ed51-8833-413f-bff5-0e139c11264a",
            "025c58cd-1b7e-43be-9ffb-8571a613579b",
            "cddf9b8f-27f9-4fe9-97cb-9e27d4fe3394",
            "3b914679-1f5e-4cbd-8044-d13d35d5236c",
            "516f91da-bd70-4351-ba6d-25e16b7713b7",
            "c4c5e3de-c0c9-4091-b242-ceb331004dfd",
            "4af6c9c9-0be0-4864-b1e9-7f87dd59ee1f",
            "12a8279d-d851-4eb9-9d64-d690455277cc",
            "118fd71b-93cd-4de5-95a4-e1485edad30e",
        ]
        film_uuids_for_far_embedding = [
            "46f15353-2add-415d-9782-fa9c5b8083d5",
            "db5dcded-29da-4c96-91a2-df1407f0a80a",
            "fda827f8-d261-4c23-9e9c-e42787580c4d",
            "57beb3fd-b1c9-4f8a-9c06-2da13f95251c",
            "b1f1e8a6-e310-47d9-a93c-6a7b192bac0e",
            "50fb4de9-e4b3-4aca-9f2f-00a48f12f9b3",
            "6e5cd268-8ce4-45f9-87d2-52f0f26edc9e",
            "b1384a92-f7fe-476b-b90b-6cec2b7a0dce",
            "c9e1f6f0-4f1e-4a76-92ee-76c1942faa97",
            "a7b11817-205f-4e1a-98b5-e3c48b824bc3",
        ]
        embeddings_near_vectors = [
            [0.0 for _ in range(384)] for _ in range(len(film_uuids_for_near_embedding))
        ]
        for i, embd in enumerate(embeddings_near_vectors):
            embd[i] = 1.0
            for before_index in range(i):
                embd[before_index] = 0.9
        uuids_and_near_vectors = list(zip(film_uuids_for_near_embedding, embeddings_near_vectors))
        embeddings_far_vectors = [
            [round(random.random(), 3) * random.choice([-1, 1]) for _ in range(384)]
            for _ in range(len(film_uuids_for_far_embedding))
        ]
        uuids_and_far_vectors = list(zip(film_uuids_for_far_embedding, embeddings_far_vectors))
        return uuids_and_near_vectors + uuids_and_far_vectors

    async def prepare_films_data(self, es_write_data):
        uuids_with_vectors = self.prepare_uuids_and_vectors()

        es_data = [
            {
                "id": uuids_with_vectors[i][0],
                "title": "Film " + str(i) + (" some horror" if i % 2 == 0 else " some triller"),
                "imdb_rating": random.randrange(1, 10) + round(random.random(), 1),
                "description": f"D {i}",
                "type": "FREE",
                "embedding": uuids_with_vectors[i][-1],
            }
            for i in range(0, 20)
        ]
        await es_write_data(es_data, test_conf.elastic.index_films, Mapping.films)
        return es_data

    @pytest.mark.parametrize(
        "payload_data, query_params, expected_answer",
        [
            (
                {"vector": [0.0 if _ != 0 else 1.0 for _ in range(384)]},
                {"page_size": 5},
                {
                    "correct_sequence_uuids": [
                        "3d825f60-9fff-4dfe-b294-1a45fa1e115d",
                        "0312ed51-8833-413f-bff5-0e139c11264a",
                        "025c58cd-1b7e-43be-9ffb-8571a613579b",
                        "cddf9b8f-27f9-4fe9-97cb-9e27d4fe3394",
                        "3b914679-1f5e-4cbd-8044-d13d35d5236c",
                    ],
                    "err_msg": "Неправльная последовательность найденных фильмов по вектору",
                },
            ),
            (
                {"vector": [1.0 for _ in range(384)]},
                {"page_size": 5},
                {
                    "correct_sequence_uuids": [
                        "118fd71b-93cd-4de5-95a4-e1485edad30e",
                        "12a8279d-d851-4eb9-9d64-d690455277cc",
                        "4af6c9c9-0be0-4864-b1e9-7f87dd59ee1f",
                        "c4c5e3de-c0c9-4091-b242-ceb331004dfd",
                        "516f91da-bd70-4351-ba6d-25e16b7713b7",
                    ],
                    "err_msg": "Неправльная последовательность найденных фильмов по вектору",
                },
            ),
        ],
        ids=[
            "Test near vectors-1",
            "Test near vectors-2",
        ],
    )
    async def test_search_valid_vectos(
        self,
        es_write_data,
        make_post_request,
        payload_data: dict[str, list[float]],
        query_params: dict[str, int],
        expected_answer: dict[str, list[str]],
    ):
        await self.prepare_films_data(es_write_data)
        body, status = await make_post_request(
            url=test_conf.asyncapi.host_service + "/internal/search-by-vector",
            data=payload_data,
            params=query_params,
        )
        assert status == HTTPStatus.OK
        uuids_from_response = [film.get("uuid", "invalid_uuid") for film in body]

        assert len(body) == len(
            expected_answer["correct_sequence_uuids"]
        ), f"Ожидалось 5 найденых фильмов, нашлось {len(body)}"

        assert uuids_from_response == expected_answer["correct_sequence_uuids"], expected_answer[
            "err_msg"
        ]
