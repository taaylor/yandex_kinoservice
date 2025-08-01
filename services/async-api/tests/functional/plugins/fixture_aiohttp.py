from json import JSONDecodeError

import aiohttp
import pytest_asyncio
from tests.functional.core.settings import test_conf


@pytest_asyncio.fixture(scope="session")
async def aiohttp_session():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest_asyncio.fixture(name="make_get_request")
def make_get_request(aiohttp_session: aiohttp.ClientSession):
    async def inner(
        uri: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> tuple[list | dict, int]:
        url = test_conf.asyncapi.host_service + uri
        async with aiohttp_session.get(url, params=params, headers=headers) as response:
            try:
                body = await response.json()
            except (JSONDecodeError, TypeError, aiohttp.ContentTypeError):
                body = []
            status = response.status
        return body, status

    return inner


@pytest_asyncio.fixture(name="make_post_request")
def make_post_request(aiohttp_session: aiohttp.ClientSession):
    async def inner(
        url: str,
        data: dict | None = None,
        params: dict | None = None,
    ) -> tuple[list | dict, int]:
        async with aiohttp_session.post(url, json=data, params=params) as response:
            try:
                body = await response.json()
            except (JSONDecodeError, TypeError, aiohttp.ContentTypeError):
                body = []
            status = response.status
        return body, status

    return inner
