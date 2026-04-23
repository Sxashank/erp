"""Account/Ledger schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema
from app.core.constants import AccountType, ControlAccountType, BalanceType


class AccountCreate(BaseSchema):
    """Schema for creating an account."""

    code: str = Field(..., min_length=1, max_length=20, description="Account code")
    name: str = Field(..., min_length=1, max_length=200, description="Account name")
    account_group_id: UUID
    account_type: AccountType = AccountType.LEDGER
    is_control_account: bool = False
    control_type: Optional[ControlAccountType] = None
    currency_code: str = "INR"
    opening_balance: Decimal = Decimal("0.00")
    opening_balance_type: Optional[BalanceType] = None
    description: Optional[str] = Field(None, max_length=500)
    gstin: Optional[str] = Field(None, max_length=15)
    pan: Optional[str] = Field(None, max_length=10)
    tds_applicable: bool = False
    tds_section: Optional[str] = Field(None, max_length=20)
    is_bank_account: bool = False
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=50)
    bank_ifsc_code: Optional[str] = Field(None, max_length=11)
    bank_branch: Optional[str] = Field(None, max_length=100)
    is_cash_account: bool = False
    allow_negative_balance: bool = True
    is_reconciliation_required: bool = False
    organization_id: UUID


class AccountUpdate(BaseSchema):
    """Schema for updating an account."""

    code: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    account_group_id: Optional[UUID] = None
    description: Optional[str] = Field(None, max_length=500)
    gstin: Optional[str] = Field(None, max_length=15)
    pan: Optional[str] = Field(None, max_length=10)
    tds_applicable: Optional[bool] = None
    tds_section: Optional[str] = Field(None, max_length=20)
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=50)
    bank_ifsc_code: Optional[str] = Field(None, max_length=11)
    bank_branch: Optional[str] = Field(None, max_length=100)
    allow_negative_balance: Optional[bool] = None
    is_reconciliation_required: Optional[bool] = None


class AccountResponse(AuditSchema):
    """Account response schema."""

    id: UUID
    code: str
    name: str
    account_group_id: UUID
    account_group_name: Optional[str] = None
    account_group_nature: Optional[str] = None
    account_type: AccountType
    is_control_account: bool
    control_type: Optional[ControlAccountType] = None
    currency_code: str
    opening_balance: Decimal
    opening_balance_type: Optional[BalanceType] = None
    current_balance: Decimal
    current_balance_type: Optional[BalanceType] = None
    description: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    tds_applicable: bool
    tds_section: Optional[str] = None
    is_bank_account: bool
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    bank_branch: Optional[str] = None
    is_cash_account: bool
    allow_negative_balance: bool
    is_reconciliation_required: bool
    is_system: bool
    organization_id: UUID


class AccountLedgerEntry(BaseSchema):
    """Single ledger entry for account statement."""

    id: UUID
    voucher_id: UUID
    voucher_number: str
    voucher_date: date
    voucher_type: str
    narration: Optional[str] = None
    debit_amount: Decimal
    credit_amount: Decimal
    running_balance: Decimal
    balance_type: BalanceType
    party_name: Optional[str] = None
    reference_number: Optional[str] = None


class AccountLedgerResponse(BaseSchema):
    """Account ledger/statement response."""

    account_id: UUID
    account_code: str
    account_name: str
    opening_balance: Decimal
    opening_balance_type: Optional[BalanceType] = None
    total_debit: Decimal
    total_credit: Decimal
    closing_balance: Decimal
    closing_balance_type: Optional[BalanceType] = None
    entries: List[AccountLedgerEntry] = []
    from_date: date
    to_date: date


class OpeningBalanceEntry(BaseSchema):
    """Single opening balance entry."""

    account_id: UUID
    opening_balance: Decimal
    opening_balance_type: BalanceType


class SetOpeningBalancesRequest(BaseSchema):
    """Request to set multiple opening balances."""

    financial_year_id: UUID
    entries: List[OpeningBalanceEntry]
