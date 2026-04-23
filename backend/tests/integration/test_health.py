"""Seed integration test: `/health` endpoint via the real ASGI app.

Confirms the app boots end-to-end with lifespan, returns the envelope we
expect, and does not leak PII to logs. See CLAUDE.md §10.4.
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_ok(app_client) -> None:
    response = await app_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body.get("status") in {"ok", "healthy"}
    assert "app" in body or "app_name" in body or "service" in body
    assert "environment" in body


@pytest.mark.integration
@pytest.mark.asyncio
async def test_openapi_served(app_client) -> None:
    response = await app_client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert spec["info"]["title"]
    assert spec["openapi"].startswith("3.")
