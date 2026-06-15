"""Schemas for borrower-portal registration & admin review.

Wire format is camelCase via :class:`CamelSchema` (CLAUDE.md §6.2 — no
floats; the Decimal stays string on the wire). Endpoints returning these
must set ``response_model_by_alias=True``.

Registration is **organisation-only** (CLAUDE.md §1). Identifiers
accepted: CIN, GSTIN, LLPIN, organisation PAN. Aadhaar / personal IDs
are never collected here.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import EmailStr, Field, model_validator

from app.models.portal.enums import PortalRegistrationStatus
from app.schemas.base import CamelSchema

# ---------------------------------------------------------------------------
# Borrower-facing
# ---------------------------------------------------------------------------


class RegisterRequest(CamelSchema):
    """``POST /portal/auth/register`` payload.

    At least one of CIN / GSTIN / LLPIN / PAN is required so the admin
    reviewer has *something* to match against an ``los_entity``.
    """

    cin: str | None = Field(None, max_length=30)
    gstin: str | None = Field(None, max_length=20)
    llpin: str | None = Field(None, max_length=20)
    pan: str | None = Field(None, max_length=20)
    loan_account_number: str | None = Field(None, max_length=80)
    sanctioned_amount: Decimal | None = Field(None, gt=0)
    authorized_signatory_name: str = Field(..., min_length=2, max_length=200)
    mobile: str = Field(..., min_length=10, max_length=15)
    email: EmailStr

    @model_validator(mode="after")
    def at_least_one_id(self) -> RegisterRequest:
        has_org_id = any([self.cin, self.gstin, self.llpin, self.pan])
        has_existing_loan = bool(self.loan_account_number and self.sanctioned_amount is not None)
        if not has_org_id and not has_existing_loan:
            raise ValueError(
                "Provide either one of cin/gstin/llpin/pan or both "
                "loanAccountNumber and sanctionedAmount"
            )
        if (self.loan_account_number is None) != (self.sanctioned_amount is None):
            raise ValueError(
                "loanAccountNumber and sanctionedAmount must be provided together"
            )
        return self


class RegisterResponse(CamelSchema):
    """Response to ``POST /register`` — OTP dispatched."""

    registration_reference: str
    status: Literal["OTP_SENT"] = "OTP_SENT"
    masked_mobile: str


class RegisterVerifyOtpRequest(CamelSchema):
    """``POST /portal/auth/register/verify-otp`` payload."""

    registration_reference: str
    otp: str = Field(..., min_length=4, max_length=8)


class RegisterVerifyOtpResponse(CamelSchema):
    """Response to ``POST /register/verify-otp``."""

    registration_reference: str
    portal_user_id: UUID
    registration_status: Literal["PENDING_APPROVAL", "ACTIVE"]
    auto_approved: bool
    linked_entity_ids: list[UUID] = Field(default_factory=list)


class RegistrationStatusResponse(CamelSchema):
    """Public status-lookup payload — no auth required."""

    registration_reference: str
    registration_status: PortalRegistrationStatus
    masked_mobile: str
    rejection_reason: str | None = None
    approved_at: datetime | None = None


# ---------------------------------------------------------------------------
# Admin-facing
# ---------------------------------------------------------------------------


class EntitySuggestion(CamelSchema):
    """One suggested ``los_entity`` to link a registration to."""

    entity_id: UUID
    legal_name: str
    cin: str | None = None
    gstin: str | None = None
    pan: str | None = None
    llpin: str | None = None
    loan_account_number: str | None = None
    sanctioned_amount: Decimal | None = None
    match_strength: Literal[
        "EXACT_LOAN_ACCOUNT",
        "EXACT_CIN",
        "EXACT_GSTIN",
        "EXACT_PAN",
        "EXACT_LLPIN",
        "FUZZY_NAME",
    ]


class AdminRegistrationListItem(CamelSchema):
    """One row of the admin list."""

    portal_user_id: UUID
    registration_reference: str
    registration_status: PortalRegistrationStatus
    requested_cin: str | None = None
    requested_gstin: str | None = None
    requested_llpin: str | None = None
    requested_pan: str | None = None
    requested_loan_account_number: str | None = None
    requested_sanctioned_amount: Decimal | None = None
    authorized_signatory_name: str
    mobile: str
    email: str
    registered_at: datetime
    approved_at: datetime | None = None
    rejection_reason: str | None = None


class AdminRegistrationListResponse(CamelSchema):
    """Paginated admin list."""

    items: list[AdminRegistrationListItem]
    total: int
    page: int
    page_size: int


class AdminRegistrationDetail(AdminRegistrationListItem):
    """Detail view with entity-match suggestions + current links."""

    suggested_entities: list[EntitySuggestion] = Field(default_factory=list)
    linked_entity_ids: list[UUID] = Field(default_factory=list)


class ApproveRequest(CamelSchema):
    """``POST /admin/portal-registrations/{id}/approve`` payload."""

    entity_ids: list[UUID] = Field(..., min_length=1)


class RejectRequest(CamelSchema):
    """``POST /admin/portal-registrations/{id}/reject`` payload."""

    reason: str = Field(..., min_length=5, max_length=500)
