"""Borrower-portal registration endpoints (unauthenticated).

* ``POST /portal/auth/register`` — kick off registration; OTP sent.
* ``POST /portal/auth/register/verify-otp`` — verify OTP, run auto-approval.
* ``GET /portal/auth/registration-status`` — self-poll by reference + mobile.

All mutating endpoints require an ``Idempotency-Key`` (CLAUDE.md §6.3).
Mounted under ``/auth`` so the URL surface is ``/api/v1/portal/auth/...``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.exceptions import BadRequestException
from app.core.rate_limit import limiter
from app.schemas.portal.registration import (
    RegisterRequest,
    RegisterResponse,
    RegisterVerifyOtpRequest,
    RegisterVerifyOtpResponse,
    RegistrationStatusResponse,
)
from app.services.portal.registration_service import PortalRegistrationService

router = APIRouter(prefix="/auth", tags=["Borrower Portal · Registration"])


def _require_idempotency_key(key: str | None) -> None:
    if not key:
        raise BadRequestException(
            "Idempotency-Key header is required for this operation",
            error_code="IDEMPOTENCY_KEY_REQUIRED",
        )


@router.post(
    "/register",
    response_model=RegisterResponse,
    response_model_by_alias=True,
    summary="Begin borrower-portal registration",
)
@limiter.limit("3/hour")
async def register(
    request: Request,
    payload: RegisterRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    """Submit organisation identifiers + signatory + contact; OTP dispatched.

    Rate-limited to 3 attempts per hour per IP. CLAUDE.md §1 — Aadhaar /
    personal-individual fields are explicitly not accepted; the request
    schema permits CIN / GSTIN / LLPIN / organisation-PAN only.
    """
    _require_idempotency_key(idempotency_key)
    service = PortalRegistrationService(db)
    result = await service.register(payload)
    await db.commit()
    return result


@router.post(
    "/register/verify-otp",
    response_model=RegisterVerifyOtpResponse,
    response_model_by_alias=True,
    summary="Verify the registration OTP",
)
async def register_verify_otp(
    payload: RegisterVerifyOtpRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
) -> RegisterVerifyOtpResponse:
    """Verify the OTP and optionally auto-approve.

    Auto-approval requires *exactly one* matching ``los_entity`` plus a
    contact record on that entity with the same mobile + email.
    Otherwise the user stays PENDING_APPROVAL for the admin queue.
    """
    _require_idempotency_key(idempotency_key)
    service = PortalRegistrationService(db)
    result = await service.verify_otp(
        registration_reference=payload.registration_reference,
        otp_code=payload.otp,
    )
    await db.commit()
    return result


@router.get(
    "/registration-status",
    response_model=RegistrationStatusResponse,
    response_model_by_alias=True,
    summary="Public registration-status lookup",
)
async def registration_status(
    reference: str = Query(..., alias="reference", min_length=10, max_length=50),
    mobile: str = Query(..., min_length=10, max_length=15),
    db: AsyncSession = Depends(get_db),
) -> RegistrationStatusResponse:
    """Status lookup. Returns 404 when reference + mobile don't match."""
    service = PortalRegistrationService(db)
    return await service.get_status(
        registration_reference=reference,
        mobile=mobile,
    )
