"""Dashboard response schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field
from app.schemas.base import CamelSchema


class AgingBucket(CamelSchema):
    """Aging bucket for AP/AR analysis."""

    label: str  # "0-30", "31-60", "61-90", "90+"
    amount: Decimal = Field(default=Decimal("0"))
    count: int = 0
    percentage: float = 0.0


class TopParty(CamelSchema):
    """Top vendor/customer by outstanding amount."""

    id: UUID
    name: str
    code: str
    outstanding: Decimal
    overdue: Decimal = Field(default=Decimal("0"))


class APSummary(CamelSchema):
    """Accounts Payable summary for dashboard."""

    total_outstanding: Decimal = Field(default=Decimal("0"))
    total_overdue: Decimal = Field(default=Decimal("0"))
    overdue_count: int = 0
    due_this_week: Decimal = Field(default=Decimal("0"))
    due_this_week_count: int = 0
    aging_buckets: List[AgingBucket] = []
    top_vendors: List[TopParty] = []

    # Period comparisons
    outstanding_change: float = 0.0  # % change from last month
    overdue_change: float = 0.0


class ARSummary(CamelSchema):
    """Accounts Receivable summary for dashboard."""

    total_outstanding: Decimal = Field(default=Decimal("0"))
    total_overdue: Decimal = Field(default=Decimal("0"))
    overdue_count: int = 0
    due_this_week: Decimal = Field(default=Decimal("0"))
    due_this_week_count: int = 0
    aging_buckets: List[AgingBucket] = []
    top_customers: List[TopParty] = []

    # Period comparisons
    outstanding_change: float = 0.0
    overdue_change: float = 0.0
    collection_rate: float = 0.0  # Collections / Opening AR


class CashFlowSummary(CamelSchema):
    """Cash flow summary for dashboard."""

    # Current balances
    total_bank_balance: Decimal = Field(default=Decimal("0"))

    # Today
    receipts_today: Decimal = Field(default=Decimal("0"))
    payments_today: Decimal = Field(default=Decimal("0"))
    net_today: Decimal = Field(default=Decimal("0"))

    # This week
    receipts_week: Decimal = Field(default=Decimal("0"))
    payments_week: Decimal = Field(default=Decimal("0"))
    net_week: Decimal = Field(default=Decimal("0"))

    # This month
    receipts_month: Decimal = Field(default=Decimal("0"))
    payments_month: Decimal = Field(default=Decimal("0"))
    net_month: Decimal = Field(default=Decimal("0"))

    # Pending cheques
    pending_cheque_receipts: Decimal = Field(default=Decimal("0"))
    pending_cheque_payments: Decimal = Field(default=Decimal("0"))


class TrendDataPoint(CamelSchema):
    """Single data point for trend charts."""

    period: str  # "Jan 2024", "Feb 2024", etc.
    value: Decimal


class TrendData(CamelSchema):
    """Trend data for charts."""

    revenue: List[TrendDataPoint] = []
    expenses: List[TrendDataPoint] = []
    collections: List[TrendDataPoint] = []
    payments: List[TrendDataPoint] = []
    net_profit: List[TrendDataPoint] = []


class RecentActivity(CamelSchema):
    """Recent transaction activity item."""

    id: UUID
    type: str  # PAYMENT, RECEIPT, INVOICE, BILL, VOUCHER
    number: str
    description: str
    amount: Decimal
    party_name: Optional[str] = None
    status: str
    created_at: datetime
    created_by_name: Optional[str] = None


class DashboardSummary(CamelSchema):
    """Overall dashboard summary."""

    # Quick stats
    total_vendors: int = 0
    total_customers: int = 0
    total_pending_approvals: int = 0

    # Financial summary
    total_revenue_mtd: Decimal = Field(default=Decimal("0"))  # Month to date
    total_expenses_mtd: Decimal = Field(default=Decimal("0"))
    net_profit_mtd: Decimal = Field(default=Decimal("0"))

    # Revenue change from last month
    revenue_change: float = 0.0
    expenses_change: float = 0.0

    # Period info
    current_financial_year: Optional[str] = None
    as_on_date: date = Field(default_factory=date.today)


class PendingApprovalItem(CamelSchema):
    """Pending approval item for dashboard widget."""

    id: UUID
    type: str  # PURCHASE_BILL, SALES_INVOICE, PAYMENT, VOUCHER
    number: str
    amount: Decimal
    party_name: Optional[str] = None
    submitted_by: str
    submitted_at: datetime
    days_pending: int = 0
