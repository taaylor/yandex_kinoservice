import os

from celery import Celery
from celery.schedules import crontab

RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "pass")

celery_engine = Celery(
    "tasks",
    broker=f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@rabbitmq-1:5672//",
    include=[
        "tasks.scheduled",
    ],
)

# Расписание запуска задач для celery beat
# Ключ в словаре может быть любым, а внутри "task": <value> value должно быть названием таски
celery_engine.conf.beat_schedule = {
    "issue.test_reminder_get_fresh_films_10_seconds": {
        "task": "issue.test_reminder_get_fresh_films_10_seconds",
        "schedule": 10,  # каждые 10 секнд
    },
    "issue.reminder_get_fresh_films_each_friday": {
        "task": "issue.reminder_get_fresh_films_each_friday",
        # каждую неделю в пятницу утром
        "schedule": crontab(minute=0, hour=9, day_of_week="fri"),
    },
}
