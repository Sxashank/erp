"""TDS Challan schemas."""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.tds.tds_challan import ChallanStatus, ChallanType


class TDSChallanBase(BaseModel):
    """Base TDS Challan schema."""

    tds_section_id: UUID
    financial_year_id: UUID
    assessment_year: str = Field(..., max_length=10, description="Assessment year e.g. 2024-25")
    period_from: date
    period_to: date
    challan_type: ChallanType = ChallanType.FORM_281
    minor_head: Optional[str] = Field(None, max_length=10)
    deductor_tan: str = Field(..., max_length=10)
    deductor_name: str = Field(..., max_length=200)
    deductor_address: Optional[str] = None
    return_quarter: Optional[str] = Field(None, max_length=10)
    remarks: Optional[str] = None


class TDSChallanCreate(TDSChallanBase):
    """Schema for creating TDS Challan."""

    organization_id: UUID
    entry_ids: List[UUID] = Field(default_factory=list, description="TDS entry IDs to include")
    # Interest and penalty can be added at creation
    interest_amount: Decimal = Decimal("0.00")
    penalty_amount: Decimal = Decimal("0.00")
    other_amount: Decimal = Decimal("0.00")


class TDSChallanUpdate(BaseModel):
    """Schema for updating TDS Challan."""

    assessment_year: Optional[str] = Field(None, max_length=10)
    period_from: Optional[date] = None
    period_to: Optional[date] = None
    challan_type: Optional[ChallanType] = None
    minor_head: Optional[str] = Field(None, max_length=10)
    deductor_tan: Optional[str] = Field(None, max_length=10)
    deductor_name: Optional[str] = Field(None, max_length=200)
    deductor_address: Optional[str] = None
    return_quarter: Optional[str] = Field(None, max_length=10)
    interest_amount: Optional[Decimal] = None
    penalty_amount: Optional[Decimal] = None
    other_amount: Optional[Decimal] = None
    remarks: Optional[str] = None


class TDSChallanPaymentUpdate(BaseModel):
    """Schema for updating challan payment details."""

    challan_number: str = Field(..., max_length=50)
    bsr_code: str = Field(..., max_length=10)
    serial_number: Optional[str] = Field(None, max_length=20)
    payment_date: date
    payment_mode: str = Field(..., max_length=20, description="ONLINE, CHEQUE, DD")
    bank_name: str = Field(..., max_length=100)
    bank_branch: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=50)
    cheque_dd_number: Optional[str] = Field(None, max_length=20)
    cheque_dd_date: Optional[date] = None


class TDSChallanOLTASUpdate(BaseModel):
    """Schema for updating OLTAS verification details."""

    oltas_acknowledgment: str = Field(..., max_length=50)
    oltas_status: str = Field(..., max_length=20)
    oltas_verified_at: date


class TDSEntryBrief(BaseModel):
    """Brief TDS entry info for challan response."""

    id: UUID
    deductee_name: str
    deductee_pan: Optional[str]
    base_amount: Decimal
    tds_amount: Decimal
    surcharge: Decimal
    cess: Decimal
    total_tds: Decimal
    deduction_date: date

    class Config:
        from_attributes = True


class TDSChallanResponse(BaseModel):
    """TDS Challan response schema."""

    id: UUID
    challan_number: Optional[str]
    bsr_code: Optional[str]
    serial_number: Optional[str]
    organization_id: UUID
    tds_section_id: UUID
    tds_section_code: Optional[str] = None
    tds_section_name: Optional[str] = None
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
    payment_date: Optional[date]
    payment_mode: Optional[str]
    bank_name: Optional[str]
    bank_branch: Optional[str]
    bank_account_number: Optional[str]
    cheque_dd_number: Optional[str]
    cheque_dd_date: Optional[date]

    # OLTAS
    oltas_acknowledgment: Optional[str]
    oltas_status: Optional[str]
    oltas_verified_at: Optional[date]

    # Form details
    challan_type: ChallanType
    minor_head: Optional[str]
    deductor_tan: str
    deductor_name: str
    deductor_address: Optional[str]

    # Return filing
    return_quarter: Optional[str]
    is_included_in_return: bool
    return_id: Optional[UUID]

    # Computed
    is_late: bool

    remarks: Optional[str]
    created_at: date
    updated_at: Optional[date]
    is_active: bool

    # Entries (optional, for detail view)
    entries: Optional[List[TDSEntryBrief]] = None

    class Config:
        from_attributes = True


class TDSChallanListResponse(BaseModel):
    """TDS Challan list response (without entries)."""

    id: UUID
    challan_number: Optional[str]
    bsr_code: Optional[str]
    organization_id: UUID
    tds_section_code: Optional[str] = None
    tds_section_name: Optional[str] = None
    assessment_year: str
    period_from: date
    period_to: date
    total_amount: Decimal
    entry_count: int
    status: ChallanStatus
    payment_date: Optional[date]
    is_late: bool
    is_included_in_return: bool
    return_quarter: Optional[str]
    created_at: date

    class Config:
        from_attributes = True


class AddEntriesToChallanRequest(BaseModel):
    """Request to add entries to an existing challan."""

    entry_ids: List[UUID] = Field(..., min_length=1)


class RemoveEntriesFromChallanRequest(BaseModel):
    """Request to remove entries from a challan."""

    entry_ids: List[UUID] = Field(..., min_length=1)


class ChallanAggregationRequest(BaseModel):
    """Request to auto-generate challans for a period."""

    organization_id: UUID
    financial_year_id: UUID
    period_from: date
    period_to: date
    tds_section_id: Optional[UUID] = Field(
        None, description="Optional: generate for specific section only"
    )
    group_by_section: bool = Field(
        True, description="Create separate challans per TDS section"
    )


class ChallanSummary(BaseModel):
    """Summary of challans for dashboard/reports."""

    total_challans: int
    draft_count: int
    pending_count: int
    paid_count: int
    verified_count: int
    total_amount_due: Decimal
    total_amount_paid: Decimal
    late_challans_count: int


class ChallanDueReport(BaseModel):
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

    class Config:
        from_attributes = True
