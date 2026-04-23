"""Regression tests for RLS tenant-context setting.

These tests enforce that `set_tenant_context` never interpolates the
organization id into raw SQL, and that it rejects non-UUID input before
any database call is issued. See CLAUDE.md §6.2 and §12.12.
"""

from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from app.database import clear_tenant_context, set_tenant_context


@pytest.mark.asyncio
async def test_set_tenant_context_uses_parameter_binding() -> None:
    """The SQL statement must carry a parameter placeholder, not a literal."""
    session = AsyncMock()
    org_id = uuid4()

    await set_tenant_context(session, org_id)

    session.execute.assert_awaited_once()
    (clause,), _ = session.execute.await_args
    compiled = str(clause)
    # The uuid must NOT appear literally in the compiled SQL.
    assert str(org_id) not in compiled
    # A bound parameter must be present.
    assert ":org_id" in compiled
    # And the bound value must match the org id as a string.
    assert clause.compile().params["org_id"] == str(org_id)


@pytest.mark.asyncio
async def test_set_tenant_context_rejects_sql_injection_payload() -> None:
    """Non-UUID payloads must be rejected by the UUID constructor before DB."""
    session = AsyncMock()
    malicious = "00000000-0000-0000-0000-000000000000'; DROP TABLE users; --"

    with pytest.raises(ValueError):
        await set_tenant_context(session, malicious)  # type: ignore[arg-type]

    session.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_tenant_context_accepts_uuid_string_form() -> None:
    """A stringified UUID is acceptable (the function coerces via UUID())."""
    session = AsyncMock()
    org_id = uuid4()

    await set_tenant_context(session, str(org_id))  # type: ignore[arg-type]

    session.execute.assert_awaited_once()
    (clause,), _ = session.execute.await_args
    assert clause.compile().params["org_id"] == str(org_id)


@pytest.mark.asyncio
async def test_clear_tenant_context_has_no_parameters() -> None:
    """Clear uses set_config with an empty string; no bindings needed."""
    session = AsyncMock()

    await clear_tenant_context(session)

    session.execute.assert_awaited_once()
    (clause,), _ = session.execute.await_args
    assert "set_config" in str(clause).lower()
