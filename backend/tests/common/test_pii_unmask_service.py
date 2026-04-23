"""Tests for `PIIUnmaskService` — the gated unmask path.

STAGE-5-PENDING-007 closure. Pairs with `test_pii_unmask.py` (which covers
the pure helpers in `app/core/pii_unmask.py`).

Contract tested here:
  - No `pii.view` permission → `ForbiddenException`, NO audit row written.
  - `pii.view` present → returns raw_value AND writes one audit row in
    the canonical shape (`event=pii_unmask`, user/org/field/record/reason).
  - Unknown field name → `UnknownPIIFieldError` (typo safety).
  - Field-specific convenience methods route through the generic path.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.exceptions import ForbiddenException
from app.services.auth.pii_service import (
    PIIUnmaskService,
    UnknownPIIFieldError,
)


class _CapturingSink:
    """AsyncSink that stashes every record it sees."""

    def __init__(self) -> None:
        self.records: list[dict] = []

    async def __call__(self, record: dict) -> None:
        self.records.append(record)


# ---------------------------------------------------------------------------
# Permission gate.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_raw_value_when_permission_granted() -> None:
    sink = _CapturingSink()
    svc = PIIUnmaskService(audit_sink=sink)
    user_id = uuid4()
    org_id = uuid4()
    record_id = uuid4()

    out = await svc.get_unmasked(
        user_permissions={"pii.view", "voucher.post"},
        user_id=user_id,
        organization_id=org_id,
        field_name="pan",
        record_type="customer",
        record_id=record_id,
        raw_value="ABCDE1234F",
        reason="CIBIL pull",
    )
    assert out == "ABCDE1234F"
    assert len(sink.records) == 1
    rec = sink.records[0]
    assert rec["event"] == "pii_unmask"
    assert rec["user_id"] == str(user_id)
    assert rec["organization_id"] == str(org_id)
    assert rec["field_name"] == "pan"
    assert rec["record_type"] == "customer"
    assert rec["record_id"] == str(record_id)
    assert rec["reason"] == "CIBIL pull"


@pytest.mark.asyncio
async def test_forbids_when_permission_missing() -> None:
    sink = _CapturingSink()
    svc = PIIUnmaskService(audit_sink=sink)

    with pytest.raises(ForbiddenException):
        await svc.get_unmasked(
            user_permissions={"voucher.post"},  # no pii.view
            user_id=uuid4(),
            organization_id=uuid4(),
            field_name="pan",
            record_type="customer",
            record_id=uuid4(),
            raw_value="ABCDE1234F",
        )
    # Denied → no audit row written.
    assert sink.records == []


@pytest.mark.asyncio
async def test_forbids_when_permissions_none() -> None:
    sink = _CapturingSink()
    svc = PIIUnmaskService(audit_sink=sink)

    with pytest.raises(ForbiddenException):
        await svc.get_unmasked(
            user_permissions=None,
            user_id=uuid4(),
            organization_id=uuid4(),
            field_name="email",
            record_type="user",
            record_id=uuid4(),
            raw_value="a@b.com",
        )
    assert sink.records == []


# ---------------------------------------------------------------------------
# Typo safety.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_field_raises_before_permission_check() -> None:
    sink = _CapturingSink()
    svc = PIIUnmaskService(audit_sink=sink)

    with pytest.raises(UnknownPIIFieldError):
        await svc.get_unmasked(
            user_permissions={"pii.view"},
            user_id=uuid4(),
            organization_id=uuid4(),
            field_name="ssn",  # not in FIELD_MASKERS
            record_type="customer",
            record_id=uuid4(),
            raw_value="000-00-0000",
        )
    assert sink.records == []


# ---------------------------------------------------------------------------
# Organization_id None — system-context readers (cron jobs).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_organization_id_none_is_recorded_as_none() -> None:
    sink = _CapturingSink()
    svc = PIIUnmaskService(audit_sink=sink)

    out = await svc.get_unmasked(
        user_permissions={"pii.view"},
        user_id="system-user",
        organization_id=None,
        field_name="email",
        record_type="user",
        record_id=uuid4(),
        raw_value="alice@example.com",
    )
    assert out == "alice@example.com"
    assert sink.records[0]["organization_id"] is None


# ---------------------------------------------------------------------------
# Field-specific convenience methods route through the generic one.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_unmasked_pan_convenience() -> None:
    sink = _CapturingSink()
    svc = PIIUnmaskService(audit_sink=sink)

    out = await svc.get_unmasked_pan(
        user_permissions={"pii.view"},
        user_id=uuid4(),
        organization_id=uuid4(),
        record_type="customer",
        record_id=uuid4(),
        raw_value="ABCDE1234F",
    )
    assert out == "ABCDE1234F"
    assert sink.records[0]["field_name"] == "pan"


@pytest.mark.asyncio
async def test_get_unmasked_aadhaar_convenience() -> None:
    sink = _CapturingSink()
    svc = PIIUnmaskService(audit_sink=sink)

    await svc.get_unmasked_aadhaar(
        user_permissions={"pii.view"},
        user_id=uuid4(),
        organization_id=uuid4(),
        record_type="entity",
        record_id=uuid4(),
        raw_value="123412341234",
    )
    assert sink.records[0]["field_name"] == "aadhaar"


@pytest.mark.asyncio
async def test_get_unmasked_bank_account_convenience() -> None:
    sink = _CapturingSink()
    svc = PIIUnmaskService(audit_sink=sink)

    await svc.get_unmasked_bank_account(
        user_permissions={"pii.view"},
        user_id=uuid4(),
        organization_id=uuid4(),
        record_type="employee",
        record_id=uuid4(),
        raw_value="55555577778888",
    )
    assert sink.records[0]["field_name"] == "bank_account_number"


# ---------------------------------------------------------------------------
# `raw_value` None is passed through (no mask vs unmask distinction).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_null_raw_value_still_audited() -> None:
    """If the underlying column is NULL the caller still asked; audit it."""
    sink = _CapturingSink()
    svc = PIIUnmaskService(audit_sink=sink)

    out = await svc.get_unmasked(
        user_permissions={"pii.view"},
        user_id=uuid4(),
        organization_id=uuid4(),
        field_name="pan",
        record_type="customer",
        record_id=uuid4(),
        raw_value=None,
    )
    assert out is None
    assert len(sink.records) == 1
    assert sink.records[0]["field_name"] == "pan"
