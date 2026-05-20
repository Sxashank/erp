"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import close_db
from app.api.v1.router import api_router
from app.core.exceptions import AppException
from app.middleware import (
    CorrelationIdMiddleware,
    RequestLoggingMiddleware,
    AuditMiddleware,
)
from app.middleware.correlation import get_correlation_id
from app.middleware.idempotency import IdempotencyMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.services.workflow import start_scheduler, stop_scheduler
from app.core.logging_config import configure_logging, get_logger
from app.core.telemetry import configure_telemetry, shutdown_telemetry

# Configure structured logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    logger.info("application_starting", app_name=settings.APP_NAME, env=settings.APP_ENV)
    # Telemetry must be configured AFTER the app is built but before it
    # starts serving. Idempotent and safe when OTEL_EXPORTER_OTLP_ENDPOINT
    # is unset (no-op mode).
    from app.database import engine as _engine

    configure_telemetry(app=app, engine=_engine)
    start_scheduler()  # Start workflow background tasks
    yield
    # Shutdown
    logger.info("application_shutting_down", app_name=settings.APP_NAME)
    stop_scheduler()  # Stop workflow background tasks
    shutdown_telemetry()
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise NBFC Management System - Backend API",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate limiting (CLAUDE.md §8.3). The slowapi middleware reads decorators
# on endpoints and enforces the limits; the exception handler shapes 429s
# into our standard error envelope.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# Error envelope (CLAUDE.md §7). Every AppException renders as
# `{error_code, message, correlation_id, details?}` so the frontend
# `showErrorToast` contract is preserved.
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    body: dict[str, object] = {
        "error_code": getattr(exc, "error_code", None) or "ERROR",
        "message": exc.detail if isinstance(exc.detail, str) else "Error",
        "correlation_id": get_correlation_id() or None,
    }
    if isinstance(exc.detail, dict):
        body["details"] = exc.detail
    return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)


# Catch-all guard: anything that escapes FastAPI's per-type handlers must still
# emit a structured envelope (and a traceback in the log) instead of falling
# through to uvicorn's plain-text "Internal Server Error" — which lacks CORS
# headers and breaks the FE error-toast contract (§7). Without this, a
# `ResponseValidationError` (or any unanticipated server bug) silently returns
# 500 with no detail, making it impossible to debug.
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    import traceback as _traceback
    logger.error(
        "unhandled_exception",
        method=request.method,
        path=request.url.path,
        error_type=type(exc).__name__,
        traceback=_traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error",
            "correlation_id": get_correlation_id() or None,
            "details": {"error_type": type(exc).__name__},
        },
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware (order matters - first added is last executed).
# We want the outermost middleware to be CorrelationId (everything else
# should see a correlation_id on the request), so it's the LAST thing added.
# Idempotency sits just inside Audit because we want the audit log to
# include the idempotency-replay branch too.
# Security headers are the OUTERMOST response middleware (innermost when
# added last / last to run on the way out), so they apply to every response
# including 4xx/5xx from the router. See CLAUDE.md §8.9.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CorrelationIdMiddleware)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }


@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs": "/docs",
        "health": "/health",
    }
