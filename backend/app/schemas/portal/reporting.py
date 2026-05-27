"""SFC borrower-portal reporting schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelSchema


class PortalReportApplicationSummary(CamelSchema):
    total: int
    submitted: int
    under_review: int
    query_pending: int
    approved: int
    released: int
    requested_amount: Decimal


class PortalReportClaimSummary(CamelSchema):
    total: int
    draft: int
    submitted: int
    verified: int
    release_in_progress: int
    released: int
    rejected: int
    released_amount: Decimal


class PortalReportStatusBreakdownItem(CamelSchema):
    status: str
    count: int


class PortalReportBorrowerBreakdownItem(CamelSchema):
    entity_id: UUID | None = None
    entity_legal_name: str
    application_count: int
    approved_count: int
    requested_amount: Decimal
    claims_released_count: int
    claims_released_amount: Decimal


class PortalReportReviewBreakdownItem(CamelSchema):
    review_owner: str
    application_count: int
    pending_sfc_review: int
    approved_count: int
    requested_amount: Decimal


class PortalReportRecentReleaseItem(CamelSchema):
    claim_id: UUID
    claim_reference: str
    entity_legal_name: str | None = None
    scheme_name: str | None = None
    applicable_subvention_amount: Decimal
    released_date: date | None = None
    release_reference: str | None = None


class PortalReportingResponse(CamelSchema):
    actor_role: str
    generated_at: datetime
    application_summary: PortalReportApplicationSummary
    claim_summary: PortalReportClaimSummary
    application_status_breakdown: list[PortalReportStatusBreakdownItem] = Field(
        default_factory=list
    )
    claim_status_breakdown: list[PortalReportStatusBreakdownItem] = Field(default_factory=list)
    borrower_breakdown: list[PortalReportBorrowerBreakdownItem] = Field(default_factory=list)
    review_breakdown: list[PortalReportReviewBreakdownItem] = Field(default_factory=list)
    recent_releases: list[PortalReportRecentReleaseItem] = Field(default_factory=list)
