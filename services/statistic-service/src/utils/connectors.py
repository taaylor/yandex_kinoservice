from contextlib import asynccontextmanager

import httpx
from db.clickhouse import ClickHouseConnector
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    ClickHouseConnector.client_httpx = httpx.AsyncClient(timeout=30)
    yield
    await ClickHouseConnector.close()
