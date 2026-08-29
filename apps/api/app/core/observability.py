from __future__ import annotations

import logging
from time import perf_counter

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.core.config import Settings

REQUESTS = Counter("opsassist_http_requests_total", "HTTP requests", ["method", "route", "status"])
LATENCY = Histogram("opsassist_http_request_duration_seconds", "HTTP request latency", ["method", "route"])
AGENT_FAILURES = Counter("opsassist_agent_failures_total", "Agent provider failures", ["agent", "provider"])


def configure_observability(app: FastAPI, settings: Settings) -> None:
    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.environment, traces_sample_rate=0.1)
    if settings.otel_exporter_otlp_endpoint:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(resource=Resource.create({"service.name": settings.otel_service_name}))
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{settings.otel_exporter_otlp_endpoint.rstrip('/')}/v1/traces")))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        started = perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        REQUESTS.labels(request.method, path, response.status_code).inc()
        LATENCY.labels(request.method, path).observe(perf_counter() - started)
        return response

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    logging.getLogger("opsassist.api").info("observability configured", extra={"otel": bool(settings.otel_exporter_otlp_endpoint)})
