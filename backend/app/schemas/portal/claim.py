"""Scheme-portal claim schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.base import CamelSchema


class BorrowerClaimDocument(CamelSchema):
    """Borrower-visible claim document descriptor."""

    document_id: UUID | None = None
    name: str
    file_name: str | None = None
    document_category: str | None = None
    uploaded_at: datetime | None = None
    download_url: str | None = None

    @model_validator(mode="after")
    def _normalize_file_name(self) -> BorrowerClaimDocument:
        if not self.file_name:
            self.file_name = self.name
        return self


class BorrowerEligibleClaimPeriod(CamelSchema):
    """One claimable period for a borrower enrollment."""

    period_start: date
    period_end: date
    label: str
    claim_frequency: str
    already_claimed: bool
    existing_claim_id: UUID | None = None
    existing_status: str | None = None


class BorrowerEligibleClaimPeriodsResponse(CamelSchema):
    """Claimable periods for one enrollment."""

    enrollment_id: UUID
    claim_frequency: str
    periods: list[BorrowerEligibleClaimPeriod] = Field(default_factory=list)


class BorrowerClaimEnrollmentItem(CamelSchema):
    """Borrower-visible scheme enrollment row."""

    enrollment_id: UUID
    loan_account_id: UUID
    loan_account_number: str | None = None
    scheme_id: UUID
    scheme_code: str | None = None
    scheme_name: str | None = None
    status: str
    enrolled_date: date
    total_claimed_to_date: Decimal
    total_paid_to_date: Decimal
    eligible_periods: list[BorrowerEligibleClaimPeriod] = Field(default_factory=list)


class BorrowerClaimEnrollmentListResponse(CamelSchema):
    """Borrower-visible enrollment list."""

    items: list[BorrowerClaimEnrollmentItem]
    total: int


class BorrowerClaimCreateRequest(CamelSchema):
    """Create a borrower claim draft."""

    enrollment_id: UUID
    period_start: date
    period_end: date
    documents: list[BorrowerClaimDocument] = Field(default_factory=list)


class BorrowerClaimSubmitRequest(CamelSchema):
    """Submit a borrower claim draft."""

    declaration_signed_at: datetime | None = None


class BorrowerClaimItem(CamelSchema):
    """Borrower-visible claim list row."""

    id: UUID
    enrollment_id: UUID
    loan_account_id: UUID | None = None
    loan_account_number: str | None = None
    scheme_id: UUID | None = None
    scheme_code: str | None = None
    claim_reference: str
    period_start: date
    period_end: date
    claim_frequency: str
    interest_paid_in_period: Decimal
    applicable_subvention_amount: Decimal
    status: str
    submitted_date: date | None = None
    verified_date: date | None = None
    release_initiated_date: date | None = None
    released_date: date | None = None
    rejection_reason: str | None = None
    release_instruction_reference: str | None = None
    release_instruction_notes: str | None = None
    release_reference: str | None = None
    declaration_signed_at: datetime | None = None
    documents: list[BorrowerClaimDocument] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def _from_orm(cls, obj: Any) -> Any:
        if isinstance(obj, dict):
            return obj
        enrollment = getattr(obj, "enrollment", None)
        loan = getattr(enrollment, "loan_account", None) if enrollment else None
        scheme = getattr(enrollment, "scheme", None) if enrollment else None
        return {
            "id": obj.id,
            "enrollment_id": obj.enrollment_id,
            "loan_account_id": getattr(loan, "id", None),
            "loan_account_number": getattr(loan, "loan_account_number", None),
            "scheme_id": getattr(scheme, "id", None),
            "scheme_code": getattr(scheme, "scheme_code", None),
            "claim_reference": obj.claim_reference,
            "period_start": obj.period_start,
            "period_end": obj.period_end,
            "claim_frequency": obj.claim_frequency,
            "interest_paid_in_period": obj.interest_paid_in_period,
            "applicable_subvention_amount": obj.applicable_subvention_amount,
            "status": obj.status,
            "submitted_date": obj.submitted_date,
            "verified_date": obj.verified_date,
            "release_initiated_date": obj.release_initiated_date,
            "released_date": obj.paid_date,
            "rejection_reason": obj.rejection_reason,
            "release_instruction_reference": obj.release_instruction_reference,
            "release_instruction_notes": obj.release_instruction_notes,
            "release_reference": obj.utr_reference,
            "declaration_signed_at": obj.declaration_signed_at,
            "documents": [
                {
                    **BorrowerClaimDocument.model_validate(doc).model_dump(by_alias=True),
                    "download_url": (
                        f"/api/v1/portal/claims/{obj.id}/documents/"
                        f"{doc.get('document_id')}/download"
                        if isinstance(doc, dict) and doc.get("document_id")
                        else None
                    ),
                }
                for doc in (obj.documents or [])
            ],
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }


class BorrowerClaimListResponse(CamelSchema):
    """Paginated borrower claim list."""

    items: list[BorrowerClaimItem]
    total: int
    page: int
    page_size: int


class BorrowerClaimStats(CamelSchema):
    """Borrower claim queue statistics."""

    draft: int
    submitted: int
    verified: int
    release_in_progress: int
    released: int
    eligible_periods: int


class BorrowerClaimsWorkbenchResponse(CamelSchema):
    """Borrower claim center aggregate response."""

    stats: BorrowerClaimStats
    enrollments: list[BorrowerClaimEnrollmentItem]
    claims: list[BorrowerClaimItem]
