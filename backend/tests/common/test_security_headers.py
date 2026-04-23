"""Security-response-header middleware tests.

CLAUDE.md §8.9. Confirms every response carries the OWASP baseline.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.middleware.security_headers import SecurityHeadersMiddleware


def _build_app() -> FastAPI:
    from fastapi import HTTPException

    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/ok")
    async def ok() -> dict:
        return {"ok": True}

    @app.get("/boom")
    async def boom() -> dict:
        # Raise an HTTPException so FastAPI returns a real 500 that flows
        # back through middleware (instead of bubbling out as an ASGI error).
        raise HTTPException(status_code=500, detail="boom")

    return app


@pytest.mark.asyncio
async def test_security_headers_present_on_ok_response() -> None:
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/ok")
    assert r.status_code == 200
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "default-src 'self'" in r.headers["content-security-policy"]
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert "camera=()" in r.headers["permissions-policy"]
    assert r.headers["x-permitted-cross-domain-policies"] == "none"


@pytest.mark.asyncio
async def test_security_headers_present_even_on_5xx() -> None:
    """Error responses must still carry security headers."""
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/boom")
    assert r.status_code == 500
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["x-content-type-options"] == "nosniff"
    assert "content-security-policy" in r.headers


@pytest.mark.asyncio
async def test_hsts_absent_on_http_in_dev() -> None:
    """HSTS must NOT be set on plain http in dev — prevents accidental
    browser pinning of localhost to https."""
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/ok")
    assert "strict-transport-security" not in r.headers


@pytest.mark.asyncio
async def test_hsts_set_on_https_in_production(monkeypatch) -> None:
    """On production + https, HSTS header is set."""
    from app.config import settings

    monkeypatch.setattr(settings, "APP_ENV", "production")
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        r = await client.get("/ok")
    assert r.headers["strict-transport-security"].startswith("max-age=31536000")
    assert "includeSubDomains" in r.headers["strict-transport-security"]


@pytest.mark.asyncio
async def test_route_can_override_csp() -> None:
    """If a route sets its own CSP, the middleware must not override it."""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/loose")
    async def loose():
        from fastapi.responses import JSONResponse

        return JSONResponse(
            {"ok": True},
            headers={"Content-Security-Policy": "default-src 'self' *.trusted.com"},
        )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/loose")
    assert r.headers["content-security-policy"] == "default-src 'self' *.trusted.com"


@pytest.mark.asyncio
async def test_server_header_stripped() -> None:
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/ok")
    # Server header must not leak framework/version.
    assert "server" not in {k.lower() for k in r.headers.keys()}
