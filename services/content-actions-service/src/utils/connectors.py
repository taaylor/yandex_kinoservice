from contextlib import asynccontextmanager

from beanie import init_beanie
from core.config import app_config
from db import cache
from fastapi import FastAPI
from models.models import Bookmark, Rating, Review, ReviewLike
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from utils.aiokafka_conn import get_broker_connector


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = AsyncIOMotorClient(
        app_config.mongodb.ASYNC_DATABASE_URL, uuidRepresentation="standard"
    )
    await init_beanie(
        database=engine[app_config.mongodb.name],
        document_models=[Rating, Review, Bookmark, ReviewLike],
    )

    cache.cache_conn = Redis(
        host=app_config.redis.host,
        port=app_config.redis.port,
        db=app_config.redis.db,
        decode_responses=True,
        username=app_config.redis.user,
        password=app_config.redis.password,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_error=False,
        retry_on_timeout=False,
    )

    broker = get_broker_connector()
    await broker.connect()

    yield

    await cache.cache_conn.close()
    engine.close()
    await broker.disconnect()
