from opentelemetry import context as context_api
from opentelemetry import trace
from opentelemetry.baggage import get_baggage, set_baggage
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.trace import Context

from .tracer_config import tracer_conf


def init_tracer(app, service_name: str):
    # Настройка семплера
    sampler = TraceIdRatioBased(tracer_conf.trace_percent)

    # Создаем ресурс с метаданными сервиса
    resource = Resource(attributes={"service.name": service_name})

    # Создаем провайдер с семплером
    provider = TracerProvider(sampler=sampler, resource=resource)

    # Создаем OTLP экспортер
    otlp_exporter = OTLPSpanExporter(
        endpoint=tracer_conf.jaeger.jaeger_url, insecure=True  # Порт для OTLP gRPC
    )

    # Добавляем оба процессора
    provider.add_span_processor(RequestIdSpanProcessor())
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    trace.set_tracer_provider(provider)


# Кастомный SpanProcessor для добавления request_id к спанам
class RequestIdSpanProcessor(SpanProcessor):

    def on_start(self, span, parent_context: Context = None):
        if parent_context is None:
            parent_context = context_api.get_current()

        # Получаем baggage из родительского контекста
        request_id = get_baggage("request_id", parent_context)
        http_method = get_baggage("http.method", parent_context)
        http_route = get_baggage("http.route", parent_context)

        if request_id:
            # Устанавливаем baggage в текущий контекст
            ctx = set_baggage("request_id", request_id)
            ctx = set_baggage("http.method", http_method, context=ctx)
            ctx = set_baggage("http.route", http_route, context=ctx)
            context_api.attach(ctx)

            # Добавляем атрибуты к спану
            span.set_attribute("http.request_id", request_id)
            span.set_attribute("http.method", http_method)
            span.set_attribute("http.route", http_route)
