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
from typing import List, Optional

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
    entity: Optional[str] = None
    amount: Decimal
    stage: Optional[str] = None
    due_date: Optional[str] = None


class UpcomingMaturityItem(CamelSchema):
    """One upcoming-maturity row."""

    id: str
    account_number: str
    entity: Optional[str] = None
    maturity_date: str
    outstanding: Decimal


class LendingDashboardResponse(CamelSchema):
    """Aggregate envelope returned by /api/v1/lending/dashboard."""

    portfolio_kpis: PortfolioKPIs
    monthly_disbursements: List[MonthlyDisbursement]
    portfolio_by_product: List[ProductSlice]
    asset_classification: List[AssetClassRow]
    pending_approvals: List[PendingApprovalItem]
    upcoming_maturities: List[UpcomingMaturityItem]
