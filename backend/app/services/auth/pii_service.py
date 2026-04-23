"""PII unmask service (STAGE-5-PENDING-007 closure).

Gates every raw-PII read through three things in sequence:

  1. Permission check: caller must hold `pii.view`, else `ForbiddenException`.
  2. Audit trail: a row is written naming WHO viewed WHAT and (if given) WHY,
     via an injected `audit_sink` callable.
  3. Return the raw value unmodified.

Pure service layer — no ORM, no endpoint glue. Callers (API handlers,
admin tools, back-office scripts) construct it with a sink that persists
the audit record however the deployment needs.

See CLAUDE.md §8.7 and `app/core/pii_unmask.py` for the primitives
(`has_pii_view`, `build_unmask_audit_record`, `FIELD_MASKERS`).
"""

from __future__ import annotations

from typing import Awaitable, Callable, Iterable, Protocol
from uuid import UUID

from app.core.exceptions import ForbiddenException
from app.core.pii_unmask import (
    FIELD_MASKERS,
    PII_VIEW_PERMISSION,
    build_unmask_audit_record,
    has_pii_view,
)


class UnknownPIIFieldError(ValueError):
    """Raised when a caller asks to unmask a field the registry doesn't know."""


class AuditSink(Protocol):
    """Anything that accepts an audit record dict and persists it.

    Typically wired to `AuditService.record(...)` at the endpoint boundary
    or to a structured-logger emit in a script context.
    """

    async def __call__(self, record: dict) -> None: ...


class PIIUnmaskService:
    """Gate raw-PII access behind a permission check + audit write.

    Construction is deliberately minimal — the only dependency is the sink
    that writes the audit record. Keeping the service stateless makes it
    trivial to reuse across endpoints and workers.
    """

    def __init__(self, audit_sink: Callable[[dict], Awaitable[None]]) -> None:
        self._audit_sink = audit_sink

    async def get_unmasked(
        self,
        *,
        user_permissions: Iterable[str] | None,
        user_id: UUID | str,
        organization_id: UUID | str | None,
        field_name: str,
        record_type: str,
        record_id: UUID | str,
        raw_value: str | None,
        reason: str | None = None,
    ) -> str | None:
        """Permission + audit + return raw.

        `field_name` must appear in `FIELD_MASKERS` (e.g. "pan", "aadhaar",
        "phone", "email", "bank_account_number", "ifsc_code"). Unknown
        fields raise `UnknownPIIFieldError` so typos don't silently bypass
        the gate.

        Returns `raw_value` unchanged after writing an audit row. If the
        caller lacks `pii.view`, raises `ForbiddenException` BEFORE writing
        any audit row (failed attempts are the caller's responsibility to
        log separately).
        """
        if field_name not in FIELD_MASKERS:
            raise UnknownPIIFieldError(
                f"{field_name!r} is not a registered PII field. "
                f"Known: {sorted(FIELD_MASKERS.keys())}"
            )

        if not has_pii_view(user_permissions):
            raise ForbiddenException(
                f"{PII_VIEW_PERMISSION} permission required to unmask "
                f"{field_name} on {record_type}:{record_id}"
            )

        record = build_unmask_audit_record(
            user_id=str(user_id),
            organization_id=str(organization_id) if organization_id is not None else None,
            field_name=field_name,
            record_type=record_type,
            record_id=str(record_id),
            reason=reason,
        )
        await self._audit_sink(record)
        return raw_value

    # Convenience shims — all delegate to `get_unmasked` with the right
    # `field_name`. Only real value is typo protection at the call site.

    async def get_unmasked_pan(
        self, *, user_permissions, user_id, organization_id,
        record_type, record_id, raw_value, reason=None,
    ) -> str | None:
        return await self.get_unmasked(
            user_permissions=user_permissions,
            user_id=user_id,
            organization_id=organization_id,
            field_name="pan",
            record_type=record_type,
            record_id=record_id,
            raw_value=raw_value,
            reason=reason,
        )

    async def get_unmasked_aadhaar(
        self, *, user_permissions, user_id, organization_id,
        record_type, record_id, raw_value, reason=None,
    ) -> str | None:
        return await self.get_unmasked(
            user_permissions=user_permissions,
            user_id=user_id,
            organization_id=organization_id,
            field_name="aadhaar",
            record_type=record_type,
            record_id=record_id,
            raw_value=raw_value,
            reason=reason,
        )

    async def get_unmasked_bank_account(
        self, *, user_permissions, user_id, organization_id,
        record_type, record_id, raw_value, reason=None,
    ) -> str | None:
        return await self.get_unmasked(
            user_permissions=user_permissions,
            user_id=user_id,
            organization_id=organization_id,
            field_name="bank_account_number",
            record_type=record_type,
            record_id=record_id,
            raw_value=raw_value,
            reason=reason,
        )
