"""Lending dashboard response schema.

Inherits ``CamelSchema`` so the JSON wire format is camelCase by default —
no per-field aliases, no FE-side mapping. Frontend consumes
``data.portfolioKpis.totalAum`` directly.

Monetary + rate fields are ``Decimal`` per CLAUDE.md §6.2 ("Float is banned
for money"). Pydantic v2 serializes ``Decimal`` to JSON as a string,
preserving every digit; the FE types those fields as ``string`` and only
parses at display time via ``AmountDisplay`` / ``PercentageDisplay``.

Endpoints returning these models MUST pass ``response_model_by_alias=True``
to the route decorator. See ``app/schemas/base.py::CamelSchema``.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import Field

from app.schemas.base import CamelSchema


class PortfolioKPIs(CamelSchema):
    """4 KPI tiles on the dashboard. Amounts in ₹, percentages as 0-100."""

    total_aum: Decimal = Field(..., description="Total AUM in INR")
    aum_growth_mom: Decimal = Field(Decimal("0"), description="Month-on-month AUM growth %")
    active_accounts: int
    sanctioned_pipeline: Decimal = Field(
        ..., description="Approved sanctions awaiting disbursement, in INR"
    )
    pending_disbursements: Decimal = Field(Decimal("0"))
    collection_efficiency: Decimal = Field(
        Decimal("0"), description="Collected / due % over the period"
    )
    overdue_amount: Decimal = Field(Decimal("0"))
    gross_npa: Decimal = Field(Decimal("0"), description="Gross NPA % (RBI definition)")
    net_npa: Decimal = Field(Decimal("0"))
    provision_coverage: Decimal = Field(Decimal("0"), description="Provision Coverage Ratio %")


class LifecycleStageMetric(CamelSchema):
    """Pipeline amount/count for one lifecycle stage."""

    stage: str
    count: int
    amount: Decimal


class TreasuryFundingSummary(CamelSchema):
    """Borrowing-side summary for source-of-funds visibility."""

    active_borrowings: int
    sanctioned_borrowings: Decimal
    drawn_borrowings: Decimal
    available_borrowings: Decimal
    borrowing_outstanding: Decimal
    weighted_cost_of_funds: Decimal


class SourceOfFundsSummary(CamelSchema):
    """Borrowing drawdowns mapped to lending deployments."""

    mapped_deployments: int
    deployed_amount: Decimal
    active_drawn_borrowings: Decimal
    unmapped_drawn_borrowings: Decimal
    weighted_cost_rate: Decimal
    weighted_lending_rate: Decimal
    weighted_spread_bps: Decimal


class MarginSummary(CamelSchema):
    """Asset yield vs liability cost and interest margin view."""

    lending_yield: Decimal
    cost_of_funds: Decimal
    gross_spread_bps: Decimal
    interest_receivable: Decimal
    interest_payable: Decimal
    net_interest_position: Decimal


class CollectionSummary(CamelSchema):
    """Current-period demand, collection, overdue and unapplied receipt view."""

    due_this_month: Decimal
    collected_this_month: Decimal
    collection_efficiency: Decimal
    overdue_amount: Decimal
    unallocated_receipts: Decimal
    unmatched_bank_credit_count: int = 0
    unmatched_bank_credit_amount: Decimal = Decimal("0")
    auto_match_candidate_count: int = 0
    match_review_required_count: int = 0


class CashflowBucket(CamelSchema):
    """Expected borrower inflows vs lender outflows for one date bucket."""

    bucket: str
    borrower_inflows: Decimal
    lender_outflows: Decimal
    net_gap: Decimal


class MonthlyDisbursement(CamelSchema):
    """One point on the trend chart. ``amount`` is in ₹ Cr."""

    month: str
    amount: Decimal


class ProductSlice(CamelSchema):
    """One slice of the AUM pie. ``value`` is in ₹ Cr."""

    name: str
    value: Decimal
    color: str


class AssetClassRow(CamelSchema):
    """One row of the asset-classification breakdown."""

    category: str
    amount: Decimal
    percentage: Decimal
    color: str


class PendingApprovalItem(CamelSchema):
    """One pending-approval row (Application / Disbursement / OTS)."""

    id: str
    type: str
    reference: str
    entity: str | None = None
    amount: Decimal
    stage: str | None = None
    due_date: str | None = None


class UpcomingMaturityItem(CamelSchema):
    """One upcoming-maturity row."""

    id: str
    account_number: str
    entity: str | None = None
    maturity_date: str
    outstanding: Decimal


class LendingDashboardResponse(CamelSchema):
    """Aggregate envelope returned by /api/v1/lending/dashboard."""

    portfolio_kpis: PortfolioKPIs
    lifecycle_pipeline: list[LifecycleStageMetric]
    treasury_funding: TreasuryFundingSummary
    source_of_funds: SourceOfFundsSummary
    margin_summary: MarginSummary
    collection_summary: CollectionSummary
    cashflow_buckets: list[CashflowBucket]
    monthly_disbursements: list[MonthlyDisbursement]
    portfolio_by_product: list[ProductSlice]
    asset_classification: list[AssetClassRow]
    pending_approvals: list[PendingApprovalItem]
    upcoming_maturities: list[UpcomingMaturityItem]
