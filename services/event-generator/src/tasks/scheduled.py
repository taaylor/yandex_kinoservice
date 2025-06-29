import asyncio

from tasks.celery_config import celery_engine


async def mock_async_task():
    await asyncio.sleep(1)
    return {"status": "ok", "broker": "rabbitmq", "detail": "ASYNC executing"}


async def mock_sync_task():
    return {"status": "ok", "broker": "rabbitmq", "detail": "SYNC executing"}


@celery_engine.task(name="issue.reminder_1day")
def remind_1day():
    result = asyncio.run(mock_async_task())
    print(result)


@celery_engine.task(name="issue.reminder_3days")
def remind_3days():
    print(mock_sync_task())


async def get_data():
    await asyncio.sleep(5)


# @celery_engine.task(name="periodic_task")
def periodic_task():
    """Пример запуска асинхронной функции внутри celery таски"""
    print(12345)
    asyncio.run(get_data())
