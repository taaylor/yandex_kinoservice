from functools import wraps
from typing import Callable

from opentelemetry import context, trace


def traced(name: str = None):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            current_context = context.get_current()
            with tracer.start_as_current_span(name or func.__name__, current_context):
                return await func(*args, **kwargs)

        return wrapper

    return decorator
