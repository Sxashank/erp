"""OpenTelemetry instrumentation.

Wires FastAPI, httpx, and SQLAlchemy into an OTLP tracer. The exporter is
configured from `OTEL_EXPORTER_OTLP_ENDPOINT`. When the env var is unset,
all instrumentation still runs but traces go to a no-op span processor —
callers can upgrade to real telemetry by setting one env var.

CLAUDE.md §6 / Appendix A Stage 6.

Usage (called once, at app startup — see `app.main`):

    from app.core.telemetry import configure_telemetry
    configure_telemetry(app, engine)

If `OTEL_EXPORTER_OTLP_ENDPOINT` is unset, the tracer is configured with
a no-op processor — tests and local dev stay silent; production flips
the single env var.
"""

from __future__ import annotations

import os
from typing import Any

import structlog
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config import settings
from app.core.feature_flags import is_disabled

logger = structlog.get_logger("telemetry")

OTLP_ENDPOINT_ENV = "OTEL_EXPORTER_OTLP_ENDPOINT"


def configure_telemetry(app: Any = None, engine: Any = None) -> bool:
    """Set up the tracer + instrumentation.

    Returns True if live export is wired, False if running in no-op mode.
    """
    if is_disabled("otel_export"):
        logger.info("otel_disabled_by_feature_flag")
        return False

    endpoint = os.environ.get(OTLP_ENDPOINT_ENV)
    service_name = settings.APP_NAME.lower().replace(" ", "-")
    environment = settings.APP_ENV

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": "0.1.0",
            "deployment.environment": environment,
        }
    )
    provider = TracerProvider(resource=resource)

    live = False
    if endpoint:
        try:
            exporter = OTLPSpanExporter(endpoint=endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            live = True
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "otel_exporter_init_failed",
                endpoint=endpoint,
                error=str(exc),
            )

    trace.set_tracer_provider(provider)

    # Idempotent instrumentation. `instrument_app` is safe to call once per
    # process; calling twice raises. Catch to make re-import in tests benign.
    if app is not None:
        try:
            FastAPIInstrumentor.instrument_app(
                app,
                excluded_urls="/health,/docs,/redoc,/openapi.json",
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("fastapi_already_instrumented", error=str(exc))

    try:
        HTTPXClientInstrumentor().instrument()
    except Exception as exc:  # noqa: BLE001
        logger.debug("httpx_already_instrumented", error=str(exc))

    if engine is not None:
        try:
            SQLAlchemyInstrumentor().instrument(
                engine=engine.sync_engine if hasattr(engine, "sync_engine") else engine,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("sqlalchemy_already_instrumented", error=str(exc))

    logger.info(
        "otel_configured",
        service_name=service_name,
        environment=environment,
        endpoint=endpoint or "(no-op — set OTEL_EXPORTER_OTLP_ENDPOINT)",
        live=live,
    )
    return live


def shutdown_telemetry() -> None:
    """Flush spans on graceful shutdown. Safe to call without prior configure."""
    provider = trace.get_tracer_provider()
    if hasattr(provider, "shutdown"):
        try:
            provider.shutdown()  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            logger.debug("otel_shutdown_failed", error=str(exc))


def get_tracer(name: str):
    """Get a tracer for the given module. Safe to call from anywhere."""
    return trace.get_tracer(name)
