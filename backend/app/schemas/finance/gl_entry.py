"""GL Entry schemas for audit trail and reporting."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field, computed_field

from app.schemas.base import BaseSchema, AuditSchema, PaginatedResponse
from app.core.constants import (
    BalanceType,
    PartyType,
    GLEntryType,
    GLEntrySourceType,
)


# =============================================================================
# Response Schemas
# =============================================================================


class GLEntryResponse(BaseSchema):
    """GL Entry response for list views."""

    id: UUID
    voucher_id: UUID
    voucher_number: str
    voucher_date: date
    entry_type: GLEntryType
    source_type: GLEntrySourceType
    source_reference: Optional[str] = None
    account_id: UUID
    account_code: str
    account_name: str
    debit_amount: Decimal
    credit_amount: Decimal
    balance_type: BalanceType
    currency_code: str = "INR"
    party_type: Optional[PartyType] = None
    party_id: Optional[UUID] = None
    party_name: Optional[str] = None
    cost_center_id: Optional[UUID] = None
    cost_center_code: Optional[str] = None
    narration: Optional[str] = None
    reference_number: Optional[str] = None
    posting_date: datetime
    is_reversed: bool = False
    organization_id: UUID

    @computed_field
    @property
    def amount(self) -> Decimal:
        """Get the entry amount (non-zero value)."""
        return self.debit_amount if self.debit_amount > 0 else self.credit_amount


class GLEntryDetailResponse(GLEntryResponse):
    """GL Entry detail response with full information."""

    voucher_line_id: Optional[UUID] = None
    source_id: Optional[UUID] = None
    exchange_rate: Decimal = Decimal("1.000000")
    base_debit_amount: Decimal = Decimal("0.00")
    base_credit_amount: Decimal = Decimal("0.00")
    financial_year_id: UUID
    period_id: UUID
    reference_date: Optional[date] = None
    reversal_entry_id: Optional[UUID] = None
    original_entry_id: Optional[UUID] = None
    reversal_date: Optional[date] = None
    posted_by: UUID
    running_balance: Optional[Decimal] = None
    running_balance_type: Optional[BalanceType] = None
    sequence_number: int
    unit_id: Optional[UUID] = None
    created_at: datetime
    metadata: Optional[dict] = None


class GLEntrySummary(BaseSchema):
    """Summary of GL entries for an account."""

    account_id: UUID
    account_code: str
    account_name: str
    total_debit: Decimal = Decimal("0.00")
    total_credit: Decimal = Decimal("0.00")
    entry_count: int = 0
    opening_balance: Decimal = Decimal("0.00")
    opening_balance_type: Optional[BalanceType] = None
    closing_balance: Decimal = Decimal("0.00")
    closing_balance_type: Optional[BalanceType] = None


class GLAccountStatement(BaseSchema):
    """Account statement with running balance."""

    account_id: UUID
    account_code: str
    account_name: str
    period_from: date
    period_to: date
    opening_balance: Decimal = Decimal("0.00")
    opening_balance_type: Optional[BalanceType] = None
    entries: List[GLEntryResponse] = []
    total_debit: Decimal = Decimal("0.00")
    total_credit: Decimal = Decimal("0.00")
    closing_balance: Decimal = Decimal("0.00")
    closing_balance_type: Optional[BalanceType] = None


class GLPartyStatement(BaseSchema):
    """Party (sub-ledger) statement."""

    party_type: PartyType
    party_id: UUID
    party_name: str
    period_from: date
    period_to: date
    opening_balance: Decimal = Decimal("0.00")
    opening_balance_type: Optional[BalanceType] = None
    entries: List[GLEntryResponse] = []
    total_debit: Decimal = Decimal("0.00")
    total_credit: Decimal = Decimal("0.00")
    closing_balance: Decimal = Decimal("0.00")
    closing_balance_type: Optional[BalanceType] = None


class GLCostCenterSummary(BaseSchema):
    """Cost center-wise GL summary."""

    cost_center_id: UUID
    cost_center_code: str
    cost_center_name: Optional[str] = None
    total_debit: Decimal = Decimal("0.00")
    total_credit: Decimal = Decimal("0.00")
    net_amount: Decimal = Decimal("0.00")
    entry_count: int = 0


class GLTrialBalanceItem(BaseSchema):
    """Trial balance line item."""

    account_id: UUID
    account_code: str
    account_name: str
    account_group_name: Optional[str] = None
    opening_debit: Decimal = Decimal("0.00")
    opening_credit: Decimal = Decimal("0.00")
    period_debit: Decimal = Decimal("0.00")
    period_credit: Decimal = Decimal("0.00")
    closing_debit: Decimal = Decimal("0.00")
    closing_credit: Decimal = Decimal("0.00")


class GLTrialBalanceResponse(BaseSchema):
    """Trial balance report response."""

    organization_id: UUID
    financial_year_id: UUID
    period_id: Optional[UUID] = None
    as_of_date: date
    items: List[GLTrialBalanceItem] = []
    total_opening_debit: Decimal = Decimal("0.00")
    total_opening_credit: Decimal = Decimal("0.00")
    total_period_debit: Decimal = Decimal("0.00")
    total_period_credit: Decimal = Decimal("0.00")
    total_closing_debit: Decimal = Decimal("0.00")
    total_closing_credit: Decimal = Decimal("0.00")
    is_balanced: bool = True


# =============================================================================
# Request/Filter Schemas
# =============================================================================


class GLEntryFilter(BaseSchema):
    """Filter for GL entry queries."""

    account_id: Optional[UUID] = None
    account_ids: Optional[List[UUID]] = None
    voucher_id: Optional[UUID] = None
    voucher_number: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    entry_type: Optional[GLEntryType] = None
    source_type: Optional[GLEntrySourceType] = None
    party_type: Optional[PartyType] = None
    party_id: Optional[UUID] = None
    cost_center_id: Optional[UUID] = None
    financial_year_id: Optional[UUID] = None
    period_id: Optional[UUID] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    include_reversed: bool = False
    unit_id: Optional[UUID] = None


class GLAccountStatementRequest(BaseSchema):
    """Request for account statement."""

    account_id: UUID
    date_from: date
    date_to: date
    include_reversed: bool = False
    include_opening_balance: bool = True


class GLPartyStatementRequest(BaseSchema):
    """Request for party statement."""

    party_type: PartyType
    party_id: UUID
    date_from: date
    date_to: date
    include_reversed: bool = False
    include_opening_balance: bool = True


class GLTrialBalanceRequest(BaseSchema):
    """Request for trial balance."""

    financial_year_id: UUID
    period_id: Optional[UUID] = None
    as_of_date: Optional[date] = None
    include_zero_balance: bool = False
    group_by_account_group: bool = True


# =============================================================================
# Internal Schemas (for service layer)
# =============================================================================


class GLEntryCreate(BaseSchema):
    """Schema for creating a GL entry (internal use)."""

    voucher_id: UUID
    voucher_line_id: Optional[UUID] = None
    voucher_number: str
    voucher_date: date
    entry_type: GLEntryType = GLEntryType.NORMAL
    source_type: GLEntrySourceType = GLEntrySourceType.MANUAL
    source_reference: Optional[str] = None
    source_id: Optional[UUID] = None
    account_id: UUID
    account_code: str
    account_name: str
    debit_amount: Decimal = Decimal("0.00")
    credit_amount: Decimal = Decimal("0.00")
    balance_type: BalanceType
    currency_code: str = "INR"
    exchange_rate: Decimal = Decimal("1.000000")
    base_debit_amount: Optional[Decimal] = None
    base_credit_amount: Optional[Decimal] = None
    party_type: Optional[PartyType] = None
    party_id: Optional[UUID] = None
    party_name: Optional[str] = None
    cost_center_id: Optional[UUID] = None
    cost_center_code: Optional[str] = None
    financial_year_id: UUID
    period_id: UUID
    narration: Optional[str] = None
    reference_number: Optional[str] = None
    reference_date: Optional[date] = None
    posting_date: datetime
    posted_by: UUID
    organization_id: UUID
    unit_id: Optional[UUID] = None
    metadata: Optional[dict] = None


class GLEntryBulkCreate(BaseSchema):
    """Schema for bulk GL entry creation (from voucher posting)."""

    voucher_id: UUID
    entries: List[GLEntryCreate]


class GLEntryReversal(BaseSchema):
    """Schema for reversing GL entries."""

    original_voucher_id: UUID
    reversal_voucher_id: UUID
    reversal_date: date
    reversal_reason: Optional[str] = None
    reversed_by: UUID


# =============================================================================
# Report Schemas
# =============================================================================


class GLDayBookEntry(BaseSchema):
    """Day book entry for daily transaction summary."""

    voucher_id: UUID
    voucher_number: str
    voucher_date: date
    voucher_type_name: Optional[str] = None
    narration: Optional[str] = None
    total_debit: Decimal
    total_credit: Decimal
    entry_count: int


class GLDayBookResponse(BaseSchema):
    """Day book report response."""

    organization_id: UUID
    date: date
    entries: List[GLDayBookEntry] = []
    total_debit: Decimal = Decimal("0.00")
    total_credit: Decimal = Decimal("0.00")
    voucher_count: int = 0


class GLSourceSummary(BaseSchema):
    """Summary by source type."""

    source_type: GLEntrySourceType
    total_debit: Decimal = Decimal("0.00")
    total_credit: Decimal = Decimal("0.00")
    entry_count: int = 0
    voucher_count: int = 0


class GLPeriodSummary(BaseSchema):
    """Period-wise GL summary."""

    period_id: UUID
    period_name: str
    period_start: date
    period_end: date
    total_debit: Decimal = Decimal("0.00")
    total_credit: Decimal = Decimal("0.00")
    entry_count: int = 0
    is_locked: bool = False


# Paginated responses
GLEntryPaginatedResponse = PaginatedResponse[GLEntryResponse]
GLEntryDetailPaginatedResponse = PaginatedResponse[GLEntryDetailResponse]
