"""Year-End Closing schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class YearEndClosingPreviewItem(BaseModel):
    """Account item in year-end preview."""

    account_id: str
    account_code: str
    account_name: str
    closing_balance: float
    balance_type: str  # "DR" or "CR"


class YearEndClosingPreviewResponse(BaseModel):
    """Preview of year-end closing process."""

    can_close: bool = False
    net_profit_loss: Decimal = Decimal("0")
    profit_loss_type: str = "PROFIT"  # "PROFIT" or "LOSS"
    retained_earnings_account_id: Optional[str] = None
    retained_earnings_account_name: Optional[str] = None
    accounts_to_carry_forward: List[YearEndClosingPreviewItem] = []
    total_accounts: int = 0
    unclosed_periods: List[str] = []
    unposted_vouchers: int = 0
    errors: List[str] = []
    warnings: List[str] = []


class YearEndClosingRequest(BaseModel):
    """Request to execute year-end closing."""

    source_financial_year_id: UUID = Field(..., description="Financial year to close")
    target_financial_year_id: UUID = Field(..., description="New financial year for opening balances")
    skip_validations: bool = Field(False, description="Skip period closure validations")


class YearEndClosingResponse(BaseModel):
    """Response after year-end closing execution."""

    success: bool = False
    message: str = ""
    net_profit_loss: Decimal = Decimal("0")
    profit_loss_type: str = "PROFIT"
    closing_voucher_id: Optional[str] = None
    closing_voucher_number: Optional[str] = None
    accounts_carried_forward: int = 0
    new_year_id: Optional[str] = None
    errors: List[str] = []
    warnings: List[str] = []


class ReopenYearRequest(BaseModel):
    """Request to reopen a closed financial year."""

    reason: str = Field(..., min_length=10, max_length=500, description="Reason for reopening")


class ReopenYearResponse(BaseModel):
    """Response after reopening a year."""

    success: bool = False
    message: str = ""
    financial_year_id: str
    financial_year_name: str
