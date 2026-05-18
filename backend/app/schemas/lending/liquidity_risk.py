"""Liquidity Risk schemas (LCR / NSFR / cash-flow ladder / funding concentration).

Wire-format is camelCase via ``CamelSchema``. Money fields are JSON strings
(serialised ``Decimal``) per CLAUDE.md §6.2 — the frontend coerces with
``Number(...)`` when arithmetic / display formatting is needed.

LCR (RBI NBFC-SBR variant of Basel III): minimum 100% (phased per RBI master
direction). NSFR: minimum 100%. Status thresholds used here are platform
defaults — they are not the regulator's gate, just our colour-coding.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from app.schemas.base import CamelSchema

# =============================================================================
# LCR (Liquidity Coverage Ratio)
# =============================================================================


class LCRComponent(CamelSchema):
    """One row in the HQLA / outflows / inflows breakdown.

    ``label`` is a human-readable category name (e.g. "Cash & balances with
    RBI", "Wholesale unsecured outflows"). ``weight`` is the RBI run-off /
    HQLA-haircut factor as a decimal (1.0 = 100%, 0.85 = 85%, 0.40 = 40%).
    ``weighted_amount`` is ``amount × weight`` rounded to 2dp.
    """

    label: str
    amount: Decimal
    weight: Decimal
    weighted_amount: Decimal


class LCRSnapshot(CamelSchema):
    """Point-in-time LCR computation. Not persisted in v1 — computed on demand."""

    as_of_date: date

    # HQLA breakdown (already weighted in each component, plus the gross total
    # for transparency).
    hqla_level_1: list[LCRComponent]
    hqla_level_2a: list[LCRComponent]
    hqla_level_2b: list[LCRComponent]
    total_hqla: Decimal  # Σ weighted_amount across all 3 levels.

    # Outflows (next 30 days) — weighted per run-off factor.
    outflows: list[LCRComponent]
    total_weighted_outflows: Decimal

    # Inflows (next 30 days) — weighted per inflow factor, capped at 75% of
    # outflows per Basel III. ``inflow_cap_applied`` indicates whether the cap
    # bound the result.
    inflows: list[LCRComponent]
    total_weighted_inflows: Decimal
    inflow_cap_applied: bool

    # Net outflow = max(outflows − min(inflows, 0.75 × outflows), 0.25 × outflows).
    net_cash_outflows: Decimal

    # LCR = HQLA / Net outflows × 100. Returned as a percent (e.g. 120.45 for
    # 120.45%). When net outflows are 0 the ratio is reported as 0 to avoid
    # division-by-zero / Infinity on the wire.
    lcr_percent: Decimal

    minimum_required_percent: Decimal  # 100.00 per RBI.

    # Platform colour-coding (NOT the regulator's gate):
    #   "ADEQUATE"   ratio >= 100%
    #   "WATCH"      80% <= ratio < 100%
    #   "BREACH"     ratio <  80%
    #   "NO_DATA"    insufficient inputs to compute (e.g. no outflows + no HQLA)
    status: str


# =============================================================================
# NSFR (Net Stable Funding Ratio)
# =============================================================================


class NSFRComponent(CamelSchema):
    """One row in the ASF / RSF breakdown."""

    label: str
    amount: Decimal
    weight: Decimal
    weighted_amount: Decimal


class NSFRSnapshot(CamelSchema):
    """Point-in-time NSFR computation. Not persisted in v1."""

    as_of_date: date

    asf_components: list[NSFRComponent]
    total_asf: Decimal

    rsf_components: list[NSFRComponent]
    total_rsf: Decimal

    nsfr_percent: Decimal
    minimum_required_percent: Decimal  # 100.00 per RBI.

    status: str  # ADEQUATE / WATCH / BREACH / NO_DATA — same scheme as LCR.


# =============================================================================
# Cash-flow Ladder (RBI ALM buckets)
# =============================================================================


class CashflowBucket(CamelSchema):
    """One ALM bucket of the cash-flow ladder.

    ``days_from`` / ``days_to`` describe the bucket boundary in days from the
    reporting date. For the terminal bucket (> 5 years) ``days_to`` is set to
    None.
    """

    bucket_label: str
    days_from: int
    days_to: int | None
    inflows: Decimal
    outflows: Decimal
    gap: Decimal  # inflows − outflows
    cumulative_gap: Decimal  # running sum of gap across buckets, oldest first


class CashflowLadderSnapshot(CamelSchema):
    """Cash-flow ladder across RBI ALM buckets."""

    as_of_date: date
    buckets: list[CashflowBucket]
    total_inflows: Decimal
    total_outflows: Decimal
    net_position: Decimal


# =============================================================================
# Funding Concentration
# =============================================================================


class FundingConcentrationItem(CamelSchema):
    """Top-N lender concentration entry.

    ``risk_flag`` is "HIGH" when a single lender accounts for > 20% of the
    NBFC's outstanding borrowings, "MEDIUM" between 10%–20%, "LOW" otherwise.
    """

    lender_id: UUID
    lender_name: str
    lender_type: str | None
    outstanding: Decimal
    percent_of_total: Decimal
    risk_flag: str


class FundingConcentrationSnapshot(CamelSchema):
    """Funding concentration: top-N lenders by outstanding."""

    as_of_date: date
    items: list[FundingConcentrationItem]
    total_outstanding: Decimal
    total_lenders: int
    high_concentration_count: int
