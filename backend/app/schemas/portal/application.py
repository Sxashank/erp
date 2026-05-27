"""Borrower-portal: loan application schemas.

Read-/-write surfaces over ``LoanApplication`` for the borrower portal.
Wire format is camelCase via :class:`CamelSchema`; monetary fields stay
``Decimal`` per CLAUDE.md §6.2.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from app.schemas.base import CamelSchema

# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class FundUtilizationLine(CamelSchema):
    """One line of the requested fund-utilization breakdown."""

    category_id: UUID
    amount: Decimal = Field(..., ge=0)
    remarks: str | None = Field(None, max_length=500)


class CreateApplicationRequest(CamelSchema):
    """``POST /portal/applications`` payload.

    Validates that the borrower's fund-utilization lines sum to exactly
    ``requestedAmount`` (±0.01 INR). The downstream service re-asserts
    the same invariant.
    """

    entity_id: UUID
    product_id: UUID
    requested_amount: Decimal = Field(..., gt=0)
    tenure_months: int = Field(..., ge=1, le=600)
    purpose_description: str = Field(..., min_length=2, max_length=500)
    detailed_purpose: str | None = Field(None, max_length=4000)
    project_name: str | None = Field(None, max_length=200)
    project_location: str | None = Field(None, max_length=500)
    project_cost: Decimal | None = Field(None, ge=0)
    shipyard_name: str | None = Field(None, max_length=200)
    maritime_segment: str | None = Field(None, max_length=200)
    declaration_accepted: bool = Field(
        ...,
        description="Borrower confirms SFC declarations and document truthfulness.",
    )
    fund_utilization: list[FundUtilizationLine] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _sum_matches_request(self) -> CreateApplicationRequest:
        if not self.fund_utilization:
            raise ValueError("fund_utilization must have at least one line")
        total = sum((ln.amount for ln in self.fund_utilization), start=Decimal("0"))
        if abs(total - self.requested_amount) > Decimal("0.01"):
            raise ValueError(
                "Sum of fund_utilization amounts must equal requested_amount " "(±0.01)"
            )
        return self


class UpdateApplicationRequest(CamelSchema):
    """Borrower-side draft update payload."""

    requested_amount: Decimal | None = Field(None, gt=0)
    tenure_months: int | None = Field(None, ge=1, le=600)
    purpose_description: str | None = Field(None, min_length=2, max_length=500)
    detailed_purpose: str | None = Field(None, max_length=4000)
    project_name: str | None = Field(None, max_length=200)
    project_location: str | None = Field(None, max_length=500)
    project_cost: Decimal | None = Field(None, ge=0)
    shipyard_name: str | None = Field(None, max_length=200)
    maritime_segment: str | None = Field(None, max_length=200)
    declaration_accepted: bool | None = None
    fund_utilization: list[FundUtilizationLine] | None = None

    model_config = ConfigDict(extra="forbid")


class ApplicationWithdrawRequest(CamelSchema):
    """Borrower-side withdrawal request."""

    reason: str = Field(..., min_length=5, max_length=1000)


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class ApplicationListItem(CamelSchema):
    """One row of the borrower's applications list."""

    id: UUID
    application_number: str
    entity_id: UUID
    entity_legal_name: str | None = None
    product_id: UUID
    product_name: str | None = None
    requested_amount: Decimal
    tenure_months: int
    purpose_description: str | None = None
    status: str
    scheme_status: str
    stage: str
    submitted_at: datetime | None = None
    decision_at: datetime | None = None
    created_at: datetime
    review_remarks: str | None = None
    rejection_reason: str | None = None


class ApplicationListResponse(CamelSchema):
    """Paginated list."""

    items: list[ApplicationListItem]
    total: int
    page: int
    page_size: int


class ApplicationDocumentResponse(CamelSchema):
    """One document on an application."""

    id: UUID
    application_id: UUID
    dms_document_id: UUID | None = None
    document_code: str
    document_name: str
    file_name: str
    file_size_bytes: int | None = None
    file_mime_type: str | None = None
    status: str
    upload_date: datetime
    document_date: date | None = None
    download_url: str | None = None


class ApplicationDocumentRequirementResponse(CamelSchema):
    """One scheme document requirement resolved against current uploads."""

    code: str
    name: str
    category: str
    required_at_stage: str
    is_mandatory: bool
    min_file_count: int = 1
    max_file_count: int = 1
    uploaded_count: int = 0
    is_uploaded: bool = False
    missing: bool = False
    help_text: str | None = None


class ApplicationStatusEvent(CamelSchema):
    """One entry of the lightweight status-timeline returned with the detail view."""

    at: datetime
    label: str
    stage: str | None = None
    status: str | None = None


class FundUtilizationResponseLine(CamelSchema):
    """One line of the fund-utilization breakdown in a detail view."""

    id: UUID
    category_id: UUID
    category_code: str | None = None
    category_label: str | None = None
    amount: Decimal
    approved_amount: Decimal | None = None
    remarks: str | None = None


class ApplicationDetailResponse(CamelSchema):
    """Detail response for one application."""

    id: UUID
    application_number: str
    entity_id: UUID
    entity_legal_name: str | None = None
    product_id: UUID
    product_name: str | None = None
    requested_amount: Decimal
    tenure_months: int
    purpose_description: str | None = None
    detailed_purpose: str | None = None
    status: str
    scheme_status: str
    stage: str
    submitted_at: datetime | None = None
    decision_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
    project_name: str | None = None
    project_location: str | None = None
    project_cost: Decimal | None = None
    shipyard_name: str | None = None
    maritime_segment: str | None = None
    declaration_accepted: bool | None = None
    review_remarks: str | None = None
    rejection_reason: str | None = None

    fund_utilization: list[FundUtilizationResponseLine] = Field(default_factory=list)
    documents: list[ApplicationDocumentResponse] = Field(default_factory=list)
    document_requirements: list[ApplicationDocumentRequirementResponse] = Field(
        default_factory=list
    )
    status_timeline: list[ApplicationStatusEvent] = Field(default_factory=list)


class ProductListItem(CamelSchema):
    """Borrower-visible product row for the SFC borrower portal."""

    id: UUID
    code: str
    name: str
    category: str
    min_amount: Decimal
    max_amount: Decimal
    min_tenure_months: int
    max_tenure_months: int
    default_tenure_months: int | None = None
    allows_moratorium: bool = False
    max_moratorium_months: int | None = None
    interest_type: str | None = None
    allowed_repayment_frequencies: list[str] = Field(default_factory=list)
    default_repayment_frequency: str | None = None
    allowed_repayment_modes: list[str] = Field(default_factory=list)
    default_repayment_mode: str | None = None
    document_requirements: list[ApplicationDocumentRequirementResponse] = Field(
        default_factory=list
    )


class UtilizationCategoryListItem(CamelSchema):
    """Borrower-visible fund-utilization category row."""

    id: UUID
    code: str
    label: str
    description: str | None = None
    sort_order: int


class UploadDocumentResponse(CamelSchema):
    """Response to a multipart document upload."""

    id: UUID
    application_id: UUID
    document_code: str
    document_name: str
    file_name: str
    file_size_bytes: int | None = None
    status: str
    upload_date: datetime
