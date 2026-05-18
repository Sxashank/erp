"""Financial report schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.schemas.base import CamelSchema


class TrialBalanceItem(CamelSchema):
    """Single item in trial balance report."""


    account_id: UUID
    account_code: str
    account_name: str
    account_group_name: str
    account_nature: str
    opening_debit: Decimal = Decimal("0")
    opening_credit: Decimal = Decimal("0")
    period_debit: Decimal = Decimal("0")
    period_credit: Decimal = Decimal("0")
    closing_debit: Decimal = Decimal("0")
    closing_credit: Decimal = Decimal("0")


class TrialBalanceResponse(CamelSchema):
    """Trial Balance report response."""


    organization_id: UUID
    organization_name: str
    financial_year_id: UUID
    financial_year_name: str
    from_date: date
    to_date: date
    as_on_date: date
    items: List[TrialBalanceItem]
    total_opening_debit: Decimal
    total_opening_credit: Decimal
    total_period_debit: Decimal
    total_period_credit: Decimal
    total_closing_debit: Decimal
    total_closing_credit: Decimal
    generated_at: datetime


class ProfitLossItem(CamelSchema):
    """Single item in P&L statement."""


    account_group_code: str
    account_group_name: str
    level: int
    amount: Decimal
    previous_amount: Optional[Decimal] = None
    children: Optional[List["ProfitLossItem"]] = None


class ProfitLossResponse(CamelSchema):
    """Profit & Loss statement response."""


    organization_id: UUID
    organization_name: str
    financial_year_id: UUID
    financial_year_name: str
    from_date: date
    to_date: date
    income_items: List[ProfitLossItem]
    expense_items: List[ProfitLossItem]
    total_income: Decimal
    total_expenses: Decimal
    net_profit_loss: Decimal
    profit_loss_type: str  # "PROFIT" or "LOSS"
    previous_year_net: Optional[Decimal] = None
    generated_at: datetime


class BalanceSheetItem(CamelSchema):
    """Single item in balance sheet."""


    account_group_code: str
    account_group_name: str
    level: int
    amount: Decimal
    previous_amount: Optional[Decimal] = None
    children: Optional[List["BalanceSheetItem"]] = None


class BalanceSheetSection(CamelSchema):
    """Section of balance sheet (Assets/Liabilities/Equity)."""


    section_name: str
    items: List[BalanceSheetItem]
    total: Decimal
    previous_total: Optional[Decimal] = None


class BalanceSheetResponse(CamelSchema):
    """Balance Sheet report response."""


    organization_id: UUID
    organization_name: str
    financial_year_id: UUID
    financial_year_name: str
    as_on_date: date
    assets: BalanceSheetSection
    liabilities: BalanceSheetSection
    equity: BalanceSheetSection
    net_profit_loss: Decimal
    total_liabilities_equity: Decimal
    is_balanced: bool
    generated_at: datetime


class AccountLedgerEntry(CamelSchema):
    """Single entry in account ledger."""


    voucher_id: UUID
    voucher_number: str
    voucher_date: date
    voucher_type: str
    narration: Optional[str]
    debit_amount: Decimal
    credit_amount: Decimal
    running_balance: Decimal
    balance_type: str  # "DR" or "CR"


class AccountLedgerResponse(CamelSchema):
    """Account ledger response."""


    account_id: UUID
    account_code: str
    account_name: str
    account_group_name: str
    organization_id: UUID
    organization_name: str
    from_date: date
    to_date: date
    opening_balance: Decimal
    opening_balance_type: str  # "DR" or "CR"
    entries: List[AccountLedgerEntry]
    total_debit: Decimal
    total_credit: Decimal
    closing_balance: Decimal
    closing_balance_type: str  # "DR" or "CR"
    generated_at: datetime


# Cash Flow Statement Schemas

class CashFlowItem(CamelSchema):
    """Single item in cash flow section."""


    label: str
    amount: Decimal
    is_subtotal: bool = False


class CashFlowSection(CamelSchema):
    """Section of cash flow statement (Operating/Investing/Financing)."""


    section_name: str
    items: List[CashFlowItem]
    net_cash_flow: Decimal


class CashFlowStatementResponse(CamelSchema):
    """Cash Flow Statement response (Indirect Method)."""


    organization_id: UUID
    organization_name: str
    financial_year_id: UUID
    financial_year_name: str
    from_date: date
    to_date: date

    # Net Profit/Loss from P&L
    net_profit_loss: Decimal
    profit_loss_type: str  # "PROFIT" or "LOSS"

    # Three sections
    operating_activities: CashFlowSection
    investing_activities: CashFlowSection
    financing_activities: CashFlowSection

    # Summary
    net_increase_in_cash: Decimal
    opening_cash_balance: Decimal
    closing_cash_balance: Decimal

    generated_at: datetime


# Day Book / Journal Register Schemas

class DayBookEntry(CamelSchema):
    """Single voucher entry in day book."""


    voucher_id: UUID
    voucher_number: str
    voucher_date: date
    voucher_type: str
    voucher_type_name: str
    narration: Optional[str]
    total_debit: Decimal
    total_credit: Decimal
    line_count: int
    status: str


class DayBookResponse(CamelSchema):
    """Day Book / Journal Register response."""


    organization_id: UUID
    organization_name: str
    from_date: date
    to_date: date
    entries: List[DayBookEntry]
    total_vouchers: int
    total_debit: Decimal
    total_credit: Decimal
    generated_at: datetime
