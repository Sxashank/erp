"""IIF (Interest Incentivization Fund) schemas.

Wire format is camelCase per ``CamelSchema`` so the frontend consumes
fields directly (CLAUDE.md §5.4). Money / rate fields stay ``Decimal``
in Python and serialise as JSON strings (Pydantic v2 default) per
CLAUDE.md §6.2 — the FE coerces only at the chart-input boundary.

All response schemas inherit ``CamelSchema``. Endpoints serving these
models MUST set ``response_model_by_alias=True`` so FastAPI emits the
camelCase aliases.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from app.core.iif_rules import (
    DEFAULT_CALCULATION_RULES,
    DEFAULT_ELIGIBILITY_RULES,
    DEFAULT_FUND_RULES,
    DEFAULT_REQUIRED_DOCUMENTS,
    DEFAULT_WORKFLOW_RULES,
)
from app.schemas.base import CamelSchema, PaginatedResponse

# =============================================================================
# Subvention Scheme
# =============================================================================


class SubventionSchemeCreate(CamelSchema):
    """Payload for POST /lending/iif/schemes (platform-admin / per-org override)."""

    scheme_code: str = Field(..., max_length=50, min_length=1)
    scheme_name: str = Field(..., max_length=200, min_length=1)
    administering_ministry: str | None = Field(None, max_length=200)
    implementing_agency: str | None = Field(None, max_length=200)

    subvention_rate_percent: Decimal = Field(..., ge=0)
    max_subvention_per_beneficiary: Decimal | None = Field(None, ge=0)
    scheme_corpus: Decimal | None = Field(None, ge=0)

    eligible_loan_types: list[str] = Field(default_factory=list)
    max_tenure_term_loan_months: int | None = Field(None, ge=1)
    max_tenure_working_capital_months: int | None = Field(None, ge=1)

    scheme_start_date: date
    scheme_end_date: date
    eligibility_window_months: int | None = Field(None, ge=1)

    claim_frequency: str = Field(..., max_length=20)
    npa_disqualification_dpd_days: int = Field(default=30, ge=0)

    calculation_rules: dict[str, Any] = Field(
        default_factory=lambda: dict(DEFAULT_CALCULATION_RULES)
    )
    eligibility_rules: dict[str, Any] = Field(
        default_factory=lambda: dict(DEFAULT_ELIGIBILITY_RULES)
    )
    required_documents: list[dict[str, Any]] = Field(
        default_factory=lambda: list(DEFAULT_REQUIRED_DOCUMENTS)
    )
    workflow_rules: dict[str, Any] = Field(default_factory=lambda: dict(DEFAULT_WORKFLOW_RULES))
    fund_rules: dict[str, Any] = Field(default_factory=lambda: dict(DEFAULT_FUND_RULES))

    description: str | None = None


class SubventionSchemeUpdate(CamelSchema):
    """Partial update payload for a subvention scheme."""

    scheme_name: str | None = Field(None, max_length=200)
    administering_ministry: str | None = Field(None, max_length=200)
    implementing_agency: str | None = Field(None, max_length=200)

    subvention_rate_percent: Decimal | None = Field(None, ge=0)
    max_subvention_per_beneficiary: Decimal | None = Field(None, ge=0)
    scheme_corpus: Decimal | None = Field(None, ge=0)

    eligible_loan_types: list[str] | None = None
    max_tenure_term_loan_months: int | None = Field(None, ge=1)
    max_tenure_working_capital_months: int | None = Field(None, ge=1)

    scheme_start_date: date | None = None
    scheme_end_date: date | None = None
    eligibility_window_months: int | None = Field(None, ge=1)

    claim_frequency: str | None = Field(None, max_length=20)
    npa_disqualification_dpd_days: int | None = Field(None, ge=0)
    calculation_rules: dict[str, Any] | None = None
    eligibility_rules: dict[str, Any] | None = None
    required_documents: list[dict[str, Any]] | None = None
    workflow_rules: dict[str, Any] | None = None
    fund_rules: dict[str, Any] | None = None
    description: str | None = None
    is_active: bool | None = None


class SubventionSchemeResponse(CamelSchema):
    """Detail / list-item response for a subvention scheme."""

    id: UUID
    organization_id: UUID | None = None

    scheme_code: str
    scheme_name: str
    administering_ministry: str | None = None
    implementing_agency: str | None = None

    subvention_rate_percent: Decimal
    max_subvention_per_beneficiary: Decimal | None = None
    scheme_corpus: Decimal | None = None

    eligible_loan_types: list[str] = Field(default_factory=list)
    max_tenure_term_loan_months: int | None = None
    max_tenure_working_capital_months: int | None = None

    scheme_start_date: date
    scheme_end_date: date
    eligibility_window_months: int | None = None

    claim_frequency: str
    npa_disqualification_dpd_days: int
    calculation_rules: dict[str, Any] = Field(default_factory=dict)
    eligibility_rules: dict[str, Any] = Field(default_factory=dict)
    required_documents: list[dict[str, Any]] = Field(default_factory=list)
    workflow_rules: dict[str, Any] = Field(default_factory=dict)
    fund_rules: dict[str, Any] = Field(default_factory=dict)
    description: str | None = None

    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    version: int


class SubventionSchemeListResponse(PaginatedResponse):
    """Paginated list response (camelCase items)."""

    items: list[SubventionSchemeResponse]


# =============================================================================
# Fund Utilization Category
# =============================================================================


class FundUtilizationCategoryCreate(CamelSchema):
    """Payload for POST /lending/iif/categories."""

    scheme_id: UUID | None = None
    code: str = Field(..., max_length=50, min_length=1)
    label: str = Field(..., max_length=200, min_length=1)
    description: str | None = None
    sort_order: int = 0


class FundUtilizationCategoryUpdate(CamelSchema):
    """Partial update payload for a category."""

    label: str | None = Field(None, max_length=200)
    description: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class FundUtilizationCategoryResponse(CamelSchema):
    """Response for a fund-utilization category."""

    id: UUID
    organization_id: UUID | None = None
    scheme_id: UUID | None = None
    code: str
    label: str
    description: str | None = None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    version: int


class FundUtilizationCategoryListResponse(PaginatedResponse):
    """Paginated list response for categories."""

    items: list[FundUtilizationCategoryResponse]


# =============================================================================
# Application Utilization
# =============================================================================


class ApplicationUtilizationLine(CamelSchema):
    """One line item inside a bulk-replace application-utilization payload."""

    category_id: UUID
    amount: Decimal = Field(..., ge=0)
    # Optional lender-approved amount per category. Populated at
    # sanction time via the bulk-replace endpoint or the dedicated
    # ``/approved`` endpoint.
    approved_amount: Decimal | None = Field(None, ge=0)
    remarks: str | None = Field(None, max_length=500)


class ApplicationUtilizationBulkReplace(CamelSchema):
    """Payload to bulk-replace utilization rows for one application.

    ``submit=True`` enforces ``SUM(amounts) == application.requested_amount``
    (±0.01); ``submit=False`` (draft) only warns on mismatch.
    """

    lines: list[ApplicationUtilizationLine] = Field(default_factory=list)
    submit: bool = False


class ApprovedBreakdownLine(CamelSchema):
    """One line of the lender-approved breakdown."""

    category_id: UUID
    approved_amount: Decimal = Field(..., ge=0)
    remarks: str | None = Field(None, max_length=500)


class ApprovedBreakdownRequest(CamelSchema):
    """Payload to set per-category ``approved_amount`` values.

    Sum must equal the latest active sanction's sanctioned_amount
    (±0.01); the service raises on mismatch.
    """

    lines: list[ApprovedBreakdownLine] = Field(default_factory=list)


class ApplicationUtilizationResponse(CamelSchema):
    """Response for an application-utilization line.

    Includes denormalized ``categoryLabel`` so the FE doesn't need a
    second round-trip to the category master.
    """

    id: UUID
    organization_id: UUID
    application_id: UUID
    category_id: UUID
    category_code: str | None = None
    category_label: str | None = None
    amount: Decimal
    approved_amount: Decimal | None = None
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    version: int

    @model_validator(mode="before")
    @classmethod
    def _from_orm(cls, obj: Any) -> Any:
        if isinstance(obj, dict):
            return obj
        category = getattr(obj, "category", None)
        return {
            "id": obj.id,
            "organization_id": obj.organization_id,
            "application_id": obj.application_id,
            "category_id": obj.category_id,
            "category_code": getattr(category, "code", None),
            "category_label": getattr(category, "label", None),
            "amount": obj.amount,
            "approved_amount": obj.approved_amount,
            "remarks": obj.remarks,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "version": obj.version,
        }


class ApplicationUtilizationListResponse(CamelSchema):
    """Wraps the per-application utilization list plus a tally line."""

    items: list[ApplicationUtilizationResponse]
    total_amount: Decimal
    requested_amount: Decimal | None = None
    difference: Decimal | None = None
    balanced: bool
    # When any line has approved_amount set, surface a parallel tally
    # so the FE can render both the borrower-requested and the
    # lender-approved sums side-by-side.
    total_approved_amount: Decimal | None = None
    sanctioned_amount: Decimal | None = None
    approved_difference: Decimal | None = None
    approved_balanced: bool | None = None


# =============================================================================
# Loan Subvention Enrollment
# =============================================================================


class LoanSubventionEnrollmentCreate(CamelSchema):
    """Payload for POST /lending/iif/enrollments — creates a PENDING_APPROVAL row."""

    loan_account_id: UUID
    scheme_id: UUID
    enrolled_date: date | None = None
    notes: str | None = None


class LoanSubventionEnrollmentUpdate(CamelSchema):
    """Partial update for an enrollment (notes / status transitions)."""

    notes: str | None = None
    rejection_reason: str | None = Field(None, max_length=500)


class EnrollmentStatusActionRequest(CamelSchema):
    """Payload for approve / reject / suspend / reinstate transitions."""

    reason: str | None = Field(None, max_length=500)


class LoanSubventionEnrollmentResponse(CamelSchema):
    """Detail / list-item response for an enrollment.

    Includes denormalized ``loanAccountNumber`` + ``entityName`` so the
    UI's enrollment list page can render without an extra fetch.
    """

    id: UUID
    organization_id: UUID
    loan_account_id: UUID
    loan_account_number: str | None = None
    entity_id: UUID | None = None
    entity_name: str | None = None
    scheme_id: UUID
    scheme_code: str | None = None
    scheme_name: str | None = None
    enrolled_date: date
    status: str
    rejection_reason: str | None = None
    total_claimed_to_date: Decimal
    total_paid_to_date: Decimal
    notes: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    version: int

    @model_validator(mode="before")
    @classmethod
    def _from_orm(cls, obj: Any) -> Any:
        if isinstance(obj, dict):
            return obj
        loan = getattr(obj, "loan_account", None)
        entity = getattr(loan, "entity", None) if loan else None
        scheme = getattr(obj, "scheme", None)
        return {
            "id": obj.id,
            "organization_id": obj.organization_id,
            "loan_account_id": obj.loan_account_id,
            "loan_account_number": getattr(loan, "loan_account_number", None),
            "entity_id": getattr(loan, "entity_id", None),
            "entity_name": getattr(entity, "legal_name", None),
            "scheme_id": obj.scheme_id,
            "scheme_code": getattr(scheme, "scheme_code", None),
            "scheme_name": getattr(scheme, "scheme_name", None),
            "enrolled_date": obj.enrolled_date,
            "status": obj.status,
            "rejection_reason": obj.rejection_reason,
            "total_claimed_to_date": obj.total_claimed_to_date,
            "total_paid_to_date": obj.total_paid_to_date,
            "notes": obj.notes,
            "is_active": obj.is_active,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "version": obj.version,
        }


class LoanSubventionEnrollmentListResponse(PaginatedResponse):
    """Paginated list response for enrollments."""

    items: list[LoanSubventionEnrollmentResponse]


class EligibilityCheckResponse(CamelSchema):
    """Result of the eligibility-check preview.

    Returns the full breakdown of each rule so the UI can highlight
    which one(s) failed even when several would have.
    """

    eligible: bool
    reasons: list[str] = Field(default_factory=list)
    checks: dict[str, bool] = Field(default_factory=dict)


# =============================================================================
# Subvention Claim
# =============================================================================


class SubventionClaimComputeRequest(CamelSchema):
    """Preview-only compute. Does not persist."""

    enrollment_id: UUID
    period_start: date
    period_end: date


class SubventionClaimComputeResponse(CamelSchema):
    """Outcome of a non-persisting compute call."""

    enrollment_id: UUID
    period_start: date
    period_end: date
    interest_paid_in_period: Decimal
    subvention_rate_percent: Decimal
    applicable_subvention_amount: Decimal
    calculation_method: str | None = None
    eligible_base_amount: Decimal | None = None


class EligibleClaimPeriod(CamelSchema):
    """One claimable period for an enrolment."""

    period_start: date
    period_end: date
    label: str  # e.g. "FY 2026 Q1 (Apr-Jun 2026)"
    claim_frequency: str
    already_claimed: bool
    existing_claim_id: UUID | None = None
    existing_status: str | None = None


class EligibleClaimPeriodResponse(CamelSchema):
    """List of periods that could be claimed next."""

    enrollment_id: UUID
    claim_frequency: str
    periods: list[EligibleClaimPeriod] = Field(default_factory=list)


class SubventionClaimDocumentInput(CamelSchema):
    """A claim-attached document descriptor (file lives in DMS)."""

    document_id: UUID | None = None
    name: str = Field(..., max_length=200)
    file_name: str | None = Field(None, max_length=255)
    document_category: str | None = Field(None, max_length=100)
    path: str | None = Field(None, max_length=500)
    uploaded_at: datetime | None = None

    @model_validator(mode="after")
    def _normalize_file_name(self) -> SubventionClaimDocumentInput:
        if not self.file_name:
            self.file_name = self.name
        return self


class SubventionClaimCreate(CamelSchema):
    """Payload for POST /lending/iif/claims — creates a DRAFT claim."""

    enrollment_id: UUID
    period_start: date
    period_end: date
    documents: list[SubventionClaimDocumentInput] = Field(default_factory=list)


class SubventionClaimUpdate(CamelSchema):
    """Partial update for a DRAFT claim (documents only)."""

    documents: list[SubventionClaimDocumentInput] | None = None


class SubventionClaimSubmitRequest(CamelSchema):
    """Payload for POST /claims/{id}/submit.

    Signing the declaration is part of submit. ``declarationSignedAt``
    defaults to the server's now() if omitted.
    """

    declaration_signed_at: datetime | None = None


class SubventionClaimVerifyRequest(CamelSchema):
    """Payload for POST /claims/{id}/verify."""

    decision: str = Field(..., pattern="^(APPROVE|REJECT)$")
    reason: str | None = Field(None, max_length=500)


class SubventionClaimInitiateReleaseRequest(CamelSchema):
    """Payload for POST /claims/{id}/initiate-release."""

    release_instruction_reference: str = Field(..., max_length=100, min_length=1)
    release_initiated_date: date | None = None
    release_instruction_notes: str | None = Field(None, max_length=500)


class SubventionClaimMarkReleasedRequest(CamelSchema):
    """Payload for POST /claims/{id}/mark-released."""

    release_reference: str = Field(..., max_length=100, min_length=1)
    released_date: date | None = None


class SubventionClaimCancelRequest(CamelSchema):
    """Payload for POST /claims/{id}/cancel."""

    reason: str = Field(..., max_length=500, min_length=1)


class SubventionClaimResponse(CamelSchema):
    """Detail / list-item response for a claim.

    Denormalized fields ``loanAccountNumber`` + ``schemeCode`` save the
    FE from a second fetch. ``documents`` is a JSON list of file blobs.
    """

    id: UUID
    organization_id: UUID
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
    declaration_signed_by: UUID | None = None
    declaration_signed_at: datetime | None = None
    documents: list[dict[str, Any]] = Field(default_factory=list)
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    version: int

    @model_validator(mode="before")
    @classmethod
    def _from_orm(cls, obj: Any) -> Any:
        if isinstance(obj, dict):
            return obj
        enrollment = getattr(obj, "enrollment", None)
        loan = getattr(enrollment, "loan_account", None) if enrollment else None
        scheme = getattr(enrollment, "scheme", None) if enrollment else None
        documents: list[dict[str, Any]] = []
        for doc in obj.documents or []:
            if not isinstance(doc, dict):
                continue
            documents.append(
                {
                    "documentId": doc.get("document_id") or doc.get("documentId"),
                    "name": doc.get("name"),
                    "fileName": doc.get("file_name") or doc.get("fileName"),
                    "documentCategory": doc.get("document_category") or doc.get("documentCategory"),
                    "path": doc.get("path"),
                    "uploadedAt": doc.get("uploaded_at") or doc.get("uploadedAt"),
                }
            )
        return {
            "id": obj.id,
            "organization_id": obj.organization_id,
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
            "declaration_signed_by": obj.declaration_signed_by,
            "declaration_signed_at": obj.declaration_signed_at,
            "documents": documents,
            "is_active": obj.is_active,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "version": obj.version,
        }


class SubventionClaimListResponse(PaginatedResponse):
    """Paginated list response for claims."""

    items: list[SubventionClaimResponse]


# =============================================================================
# Claim Report
# =============================================================================


class InterestCalculationLine(CamelSchema):
    """One tranche-wise row of the interest calculation sheet."""

    tranche_number: int
    disbursement_reference: str | None = None
    disbursed_amount: Decimal
    disbursement_date: date | None = None
    opening_balance: Decimal
    interest_rate: Decimal
    interest_for_period: Decimal
    eligible_subvention: Decimal


class RepaymentRecordLine(CamelSchema):
    """One installment-wise row of the borrower repayment record."""

    receipt_number: str
    value_date: date
    receipt_amount: Decimal
    installment_number: int | None = None
    due_date: date | None = None
    installment_status: str | None = None
    emi_amount: Decimal | None = None
    principal_due: Decimal | None = None
    interest_due: Decimal | None = None
    penal_due: Decimal | None = None
    allocated_to_interest: Decimal
    allocated_to_principal: Decimal
    allocated_to_penal: Decimal
    allocated_to_charges: Decimal
    instrument_number: str | None = None


class ClaimReportHeader(CamelSchema):
    """Top block of the claim report."""

    scheme_code: str
    scheme_name: str
    implementing_agency: str | None = None
    administering_ministry: str | None = None
    borrower_entity_id: UUID | None = None
    borrower_entity_name: str | None = None
    loan_account_id: UUID | None = None
    loan_account_number: str | None = None
    sanction_date: date | None = None
    tenure_months: int | None = None
    period_start: date
    period_end: date
    claim_frequency: str


class ClaimReportFooter(CamelSchema):
    """Bottom block of the claim report."""

    claim_reference: str
    generated_at: datetime
    version: str = "1.0"


class ClaimAccountStatus(CamelSchema):
    """Account-status snapshot at report-build time."""

    asset_classification: str | None = None
    days_past_due: int | None = None
    last_emi_status: str | None = None


class ClaimReportResponse(CamelSchema):
    """Top-level structured claim report payload."""

    header: ClaimReportHeader
    interest_calculation: list[InterestCalculationLine] = Field(default_factory=list)
    repayment_record: list[RepaymentRecordLine] = Field(default_factory=list)
    account_status: ClaimAccountStatus
    declaration_text: str
    declaration_signed_by: UUID | None = None
    declaration_signed_at: datetime | None = None
    summary: dict[str, Any] = Field(default_factory=dict)
    footer: ClaimReportFooter
