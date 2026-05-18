"""TDS Challan schemas."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.models.tds.tds_challan import ChallanStatus, ChallanType
from app.schemas.base import CamelSchema


class TDSChallanBase(CamelSchema):
    """Base TDS Challan schema."""

    tds_section_id: UUID
    financial_year_id: UUID
    assessment_year: str = Field(..., max_length=10, description="Assessment year e.g. 2024-25")
    period_from: date
    period_to: date
    challan_type: ChallanType = ChallanType.FORM_281
    minor_head: str | None = Field(None, max_length=10)
    deductor_tan: str = Field(..., max_length=10)
    deductor_name: str = Field(..., max_length=200)
    deductor_address: str | None = None
    return_quarter: str | None = Field(None, max_length=10)
    remarks: str | None = None


class TDSChallanCreate(TDSChallanBase):
    """Schema for creating TDS Challan."""

    organization_id: UUID
    entry_ids: list[UUID] = Field(default_factory=list, description="TDS entry IDs to include")
    # Interest and penalty can be added at creation
    interest_amount: Decimal = Decimal("0.00")
    penalty_amount: Decimal = Decimal("0.00")
    other_amount: Decimal = Decimal("0.00")


class TDSChallanUpdate(CamelSchema):
    """Schema for updating TDS Challan."""

    assessment_year: str | None = Field(None, max_length=10)
    period_from: date | None = None
    period_to: date | None = None
    challan_type: ChallanType | None = None
    minor_head: str | None = Field(None, max_length=10)
    deductor_tan: str | None = Field(None, max_length=10)
    deductor_name: str | None = Field(None, max_length=200)
    deductor_address: str | None = None
    return_quarter: str | None = Field(None, max_length=10)
    interest_amount: Decimal | None = None
    penalty_amount: Decimal | None = None
    other_amount: Decimal | None = None
    remarks: str | None = None


class TDSChallanPaymentUpdate(CamelSchema):
    """Schema for updating challan payment details."""

    challan_number: str = Field(..., max_length=50)
    bsr_code: str = Field(..., max_length=10)
    serial_number: str | None = Field(None, max_length=20)
    payment_date: date
    payment_mode: str = Field(..., max_length=20, description="ONLINE, CHEQUE, DD")
    bank_name: str = Field(..., max_length=100)
    bank_branch: str | None = Field(None, max_length=100)
    bank_account_number: str | None = Field(None, max_length=50)
    cheque_dd_number: str | None = Field(None, max_length=20)
    cheque_dd_date: date | None = None


class TDSChallanOLTASUpdate(CamelSchema):
    """Schema for updating OLTAS verification details."""

    oltas_acknowledgment: str = Field(..., max_length=50)
    oltas_status: str = Field(..., max_length=20)
    oltas_verified_at: date


class TDSEntryBrief(CamelSchema):
    """Brief TDS entry info for challan response."""

    id: UUID
    deductee_name: str
    deductee_pan: str | None
    base_amount: Decimal
    tds_amount: Decimal
    surcharge: Decimal
    cess: Decimal
    total_tds: Decimal
    deduction_date: date


class TDSChallanResponse(CamelSchema):
    """TDS Challan response schema."""

    id: UUID
    challan_number: str | None
    bsr_code: str | None
    serial_number: str | None
    organization_id: UUID
    tds_section_id: UUID
    tds_section_code: str | None = None
    tds_section_name: str | None = None
    financial_year_id: UUID
    assessment_year: str
    period_from: date
    period_to: date

    # Amounts
    total_base_amount: Decimal
    total_tds_amount: Decimal
    total_surcharge: Decimal
    total_cess: Decimal
    interest_amount: Decimal
    penalty_amount: Decimal
    other_amount: Decimal
    total_amount: Decimal

    # Entry count
    entry_count: int

    # Status and payment
    status: ChallanStatus
    payment_date: date | None
    payment_mode: str | None
    bank_name: str | None
    bank_branch: str | None
    bank_account_number: str | None
    cheque_dd_number: str | None
    cheque_dd_date: date | None

    # OLTAS
    oltas_acknowledgment: str | None
    oltas_status: str | None
    oltas_verified_at: date | None

    # Form details
    challan_type: ChallanType
    minor_head: str | None
    deductor_tan: str
    deductor_name: str
    deductor_address: str | None

    # Return filing
    return_quarter: str | None
    is_included_in_return: bool
    return_id: UUID | None

    # Computed
    is_late: bool

    remarks: str | None
    created_at: date
    updated_at: date | None
    is_active: bool

    # Entries (optional, for detail view)
    entries: list[TDSEntryBrief] | None = None


class TDSChallanListResponse(CamelSchema):
    """TDS Challan list response (without entries)."""

    id: UUID
    challan_number: str | None
    bsr_code: str | None
    organization_id: UUID
    tds_section_code: str | None = None
    tds_section_name: str | None = None
    assessment_year: str
    period_from: date
    period_to: date
    total_amount: Decimal
    entry_count: int
    status: ChallanStatus
    payment_date: date | None
    is_late: bool
    is_included_in_return: bool
    return_quarter: str | None
    created_at: date


class AddEntriesToChallanRequest(CamelSchema):
    """Request to add entries to an existing challan."""

    entry_ids: list[UUID] = Field(..., min_length=1)


class RemoveEntriesFromChallanRequest(CamelSchema):
    """Request to remove entries from a challan."""

    entry_ids: list[UUID] = Field(..., min_length=1)


class ChallanAggregationRequest(CamelSchema):
    """Request to auto-generate challans for a period."""

    organization_id: UUID
    financial_year_id: UUID
    period_from: date
    period_to: date
    tds_section_id: UUID | None = Field(
        None, description="Optional: generate for specific section only"
    )
    group_by_section: bool = Field(
        True, description="Create separate challans per TDS section"
    )


class ChallanSummary(CamelSchema):
    """Summary of challans for dashboard/reports."""

    total_challans: int
    draft_count: int
    pending_count: int
    paid_count: int
    verified_count: int
    total_amount_due: Decimal
    total_amount_paid: Decimal
    late_challans_count: int


class ChallanDueReport(CamelSchema):
    """Report of challans due for payment."""

    id: UUID
    tds_section_code: str
    assessment_year: str
    period_from: date
    period_to: date
    total_amount: Decimal
    entry_count: int
    due_date: date
    days_overdue: int
    interest_applicable: Decimal
