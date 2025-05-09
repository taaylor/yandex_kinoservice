import logging
import uuid

from fastapi import Request
from opentelemetry import context
from opentelemetry.baggage import set_baggage
from opentelemetry.trace import Span, get_current_span

logger = logging.getLogger(__name__)


async def request_id_middleware(request: Request, call_next):
    token = None
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = f"service:{str(uuid.uuid4())}"
        logger.warning(
            f"Отсутствует заголовок X-Request-ID в запросе к {request.method} {request.url.path}. "
            f"Сгенерирован request_id: {request_id}"
        )
    else:
        request_id = f"nginx:{request_id}"

    # Проверяем, есть ли активный спан
    current_span = get_current_span()
    if isinstance(current_span, Span) and current_span.is_recording():
        # Создаем контекст с baggage только если трассировка активна
        ctx = set_baggage("request_id", request_id)
        ctx = set_baggage("http.method", request.method, context=ctx)
        ctx = set_baggage("http.route", request.url.path, context=ctx)
        token = context.attach(ctx)

    try:
        response = await call_next(request)
        return response
    finally:
        if token:
            context.detach(token)
