"""Credit-risk cockpit response schemas for corporate lending."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelSchema


class RiskCockpitSummary(CamelSchema):
    """Portfolio-level risk, overdue and provisioning summary."""

    total_accounts: int
    total_outstanding: Decimal
    overdue_accounts: int
    overdue_amount: Decimal
    sma_accounts: int
    sma_amount: Decimal
    npa_accounts: int
    npa_amount: Decimal
    gross_npa_percent: Decimal = Field(..., description="Gross NPA / total outstanding")
    provision_required: Decimal
    provision_held: Decimal
    provision_gap: Decimal
    provision_coverage_percent: Decimal


class RiskBucketMetric(CamelSchema):
    """Outstanding and provisioning by RBI asset classification."""

    classification: str
    label: str
    account_count: int
    outstanding: Decimal
    portfolio_percent: Decimal
    provision_required: Decimal
    provision_held: Decimal
    provision_gap: Decimal
    provision_coverage_percent: Decimal


class OverdueBandMetric(CamelSchema):
    """DPD band metric used by management and collections teams."""

    band: str
    label: str
    account_count: int
    outstanding: Decimal
    portfolio_percent: Decimal


class TopRiskExposure(CamelSchema):
    """Large overdue/NPA exposure requiring management attention."""

    loan_account_id: UUID
    loan_account_number: str
    borrower_name: str
    asset_classification: str
    days_past_due: int
    total_outstanding: Decimal
    overdue_amount: Decimal
    provision_required: Decimal
    provision_held: Decimal
    provision_coverage_percent: Decimal
    npa_date: str | None = None
    oldest_due_date: str | None = None


class RiskCockpitResponse(CamelSchema):
    """Aggregate envelope returned by /api/v1/lending/risk-cockpit."""

    summary: RiskCockpitSummary
    asset_classification: list[RiskBucketMetric]
    overdue_bands: list[OverdueBandMetric]
    top_exposures: list[TopRiskExposure]
