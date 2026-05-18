"""Regulatory report schemas — CRAR composition, trend, and NBFC-IFC ratio.

These schemas are the typed contract for the three CRAR sub-section
endpoints under `/api/v1/reports/regulatory/crar/*`. See
`app/services/reports/regulatory_report_service.py` for the
implementation that emits them.

CLAUDE.md §6.2: monetary amounts are `Decimal` (NUMERIC(18,2)),
percentages are `Decimal` (NUMERIC(9,4)). Pydantic serialises Decimals
as JSON strings by default — the frontend types accept `number | string`
to absorb that boundary.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from app.schemas.base import CamelSchema

# ─────────────────────── Capital Composition ───────────────────────

CapitalTier = Literal["TIER_1", "TIER_2"]


class CapitalCompositionLine(CamelSchema):
    """One line in the capital-composition table.

    `is_subtotal` flags rows that are themselves a sum of preceding
    items in the same tier (e.g. "Sub-total: Core Tier-1") so the UI
    can render them with separator + emphasis. Deductions are emitted
    as negative `amount` values.
    """


    label: str
    amount: Decimal
    is_subtotal: bool = False
    tier: CapitalTier


class CapitalCompositionResponse(CamelSchema):
    """Tier-1 + Tier-2 capital breakdown that ladders up to total capital."""


    as_of_date: date
    generated_at: datetime
    organization_id: UUID
    tier_1_lines: list[CapitalCompositionLine]
    tier_1_total: Decimal
    tier_2_lines: list[CapitalCompositionLine]
    tier_2_total: Decimal
    total_capital: Decimal


# ─────────────────────── CRAR Trend ───────────────────────


class CapitalSnapshotItem(CamelSchema):
    """One historical snapshot row, projected for the trend chart."""


    snapshot_date: date
    tier_1_capital: Decimal
    tier_2_capital: Decimal
    total_capital: Decimal
    credit_risk_rwa: Decimal
    market_risk_rwa: Decimal
    operational_risk_rwa: Decimal
    total_rwa: Decimal
    crar: Decimal
    tier_1_ratio: Decimal


class CrarTrendResponse(CamelSchema):
    """Historical CRAR series for the regulatory dashboard."""


    organization_id: UUID
    months: int
    generated_at: datetime
    snapshots: list[CapitalSnapshotItem]


# ─────────────────────── NBFC-IFC Infrastructure Ratio ───────────────────────

InfraStatus = Literal["QUALIFIED", "AT_RISK", "NOT_QUALIFIED"]


class InfrastructureRatioResponse(CamelSchema):
    """NBFC-IFC eligibility — infrastructure book ≥ 75% of total loans."""


    as_of_date: date
    generated_at: datetime
    organization_id: UUID
    infrastructure_loans_amount: Decimal
    total_loans_amount: Decimal
    infrastructure_ratio_percent: Decimal
    minimum_required_percent: Decimal
    status: InfraStatus
