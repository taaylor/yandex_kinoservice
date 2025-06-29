from celery import Celery
from celery.schedules import crontab

# celery -A tasks.celery_config:celery_engine flower
# redis://<USER>:<PASSWORD>@<HOST>:<PORT>/<DB>
"""
amqp://<USER>:<PASSWORD>@<HOST>:<PORT>/<VHOST>
amqp://rabbit:rabbit@rabbitmq:5672//
rabbit — логин
rabbit — пароль
rabbitmq — имя сервиса в Docker Compose
5672 — порт RabbitMQ
!   // — это корневой виртуальный хост (vhost). Одна косая черта — путь, вторая — пустой vhost
"""
celery_engine = Celery(
    "tasks",
    # broker="redis://redis:6379",
    # broker="redis://redis_user:Parol123@redis:6379/0",
    broker="amqp://rabbit:rabbit@rabbitmq:5672//",
    include=[
        "tasks.scheduled",
    ],
)

# Расписание запуска задач для celery beat
# Ключ в словаре может быть любым, а внутри "task": <value> value должно быть названием таски
celery_engine.conf.beat_schedule = {
    "issue.reminder_1day": {
        "task": "issue.reminder_1day",
        "schedule": 10,  # каждые 10 секнд
        # "schedule": crontab(minute="0", hour="9"),  # каждое утро в 9:00
    },
    "issue.reminder_3days": {
        "task": "issue.reminder_3days",
        "schedule": crontab(minute="0", hour="13"),  # каждый день в 13:00
    },
    # "luboe-nazvanie": {
    #     "task": "periodic_task",
    #     "schedule": 5,  # секунды
    #     # "schedule": crontab(minute="30", hour="15"),
    # }
}
