import multiprocessing  # noqa: F401

from core.config import app_config

# Количество воркеров (процессов), обрабатывающих запросы
# workers = multiprocessing.cpu_count() * 2 + 1
workers = 1

worker_class = app_config.server.worker_class

# Какой хост и порт будет слушать Gunicorn
bind = f"{app_config.server.host}:{app_config.server.port}"

# Таймаут для обработки запроса (в секундах)
timeout = app_config.server.timeout

# Очередь входящих запросов перед обработкой
backlog = app_config.server.backlog

# Сколько запросов обработает воркер перед перезапуском
max_requests = app_config.server.max_requests

# Разброс количества запросов до перезапуска воркера
# Если max_requests = 1000, то воркеры перезапустятся случайно после 950-1050 запросов
# Это предотвращает одновременный перезапуск всех воркеров
max_requests_jitter = app_config.server.max_requests
