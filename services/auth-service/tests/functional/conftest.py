pytest_plugins = [
    "tests.functional.plugins.fixture_asyncio",
    "tests.functional.plugins.fixture_redis",
    "tests.functional.plugins.fixture_aiohttp",
    "tests.functional.plugins.fixture_postgres",
    "tests.functional.plugins.fixture_createuser",
    "tests.functional.plugins.fixture_create_all_roles",
]
