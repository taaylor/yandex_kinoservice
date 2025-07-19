import multiprocessing  # noqa: F401

from core.config import app_config

# workers = multiprocessing.cpu_count() * 2 + 1
workers = 1
worker_class = app_config.server.worker_class
bind = f"{app_config.server.host}:{app_config.server.port}"
timeout = app_config.server.timeout
backlog = app_config.server.backlog
max_requests = app_config.server.max_requests
max_requests_jitter = app_config.server.max_requests
