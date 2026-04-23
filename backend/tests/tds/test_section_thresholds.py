"""TDS threshold-validation golden tests (STAGE-4-PENDING-005 closure, part 2).

Pairs with `test_tds_rate_selection.py` (rate selection + surcharge).
This file pins `TDSEntryService.validate_threshold` — the branching logic
that decides whether a payment crosses a Section's single-transaction
threshold, its annual aggregate threshold, or both, or neither.

Thresholds are read from `mst_tds_section` (see CLAUDE.md §4.6) — never
hardcoded in code. These tests exercise the pure decision logic against a
mocked repo so they stay unit-level (no DB).

Boundary cases tested:
- `single_threshold > 0` and payment exactly equals threshold → crossed.
- Payment just below single threshold → NOT crossed (unless annual does).
- Annual aggregate crosses on the new payment → crossed (reason=AGGREGATE).
- Both thresholds zero → always applicable (reason=NO_THRESHOLD).
- No vendor → no aggregate lookup; single threshold alone decides.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.core.constants import TDSDeducteeType
from app.services.tds.tds_entry_service import TDSEntryService


ORG_ID = UUID("11111111-1111-1111-1111-111111111111")


def _section(
    *,
    code: str = "194C",
    threshold_single: Decimal = Decimal("0"),
    threshold_annual: Decimal = Decimal("0"),
    rate_individual: Decimal = Decimal("1.00"),
    rate_company: Decimal = Decimal("2.00"),
    rate_no_pan: Decimal = Decimal("20.00"),
    cess_rate: Decimal = Decimal("4.00"),
    surcharge_applicable: bool = False,
    surcharge_slabs: list | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        code=code,
        threshold_single=threshold_single,
        threshold_annual=threshold_annual,
        rate_individual=rate_individual,
        rate_company=rate_company,
        rate_no_pan=rate_no_pan,
        cess_rate=cess_rate,
        surcharge_applicable=surcharge_applicable,
        surcharge_slabs=surcharge_slabs,
    )


@pytest.fixture
def service() -> TDSEntryService:
    svc = TDSEntryService(session=MagicMock())
    svc.section_repo = MagicMock()
    svc.repo = MagicMock()
    # Default: no FY found, zero aggregate. Individual tests override.
    svc.repo.get_financial_year_for_date = AsyncMock(return_value=None)
    svc.repo.get_vendor_aggregate = AsyncMock(return_value=Decimal("0"))
    return svc


# ---------------------------------------------------------------------------
# Single-transaction threshold.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_single_threshold_crossed_at_boundary(service: TDSEntryService) -> None:
    """194C: single-transaction threshold ₹30,000. Payment exactly ₹30k → crossed."""
    section = _section(code="194C", threshold_single=Decimal("30000"))
    service.section_repo.get = AsyncMock(return_value=section)
    result = await service.validate_threshold(
        organization_id=ORG_ID,
        vendor_id=None,
        tds_section_id=section.id,
        base_amount=Decimal("30000"),
        deduction_date=date(2026, 4, 10),
        deductee_type=TDSDeducteeType.INDIVIDUAL,
        has_pan=True,
    )
    assert result.tds_applicable is True
    assert result.reason == "SINGLE_THRESHOLD"
    assert result.single_threshold == Decimal("30000")


@pytest.mark.asyncio
async def test_single_threshold_not_crossed_just_below(service: TDSEntryService) -> None:
    """194C: ₹29,999.99 → NOT crossed (no annual aggregate)."""
    section = _section(code="194C", threshold_single=Decimal("30000"))
    service.section_repo.get = AsyncMock(return_value=section)
    result = await service.validate_threshold(
        organization_id=ORG_ID,
        vendor_id=None,
        tds_section_id=section.id,
        base_amount=Decimal("29999.99"),
        deduction_date=date(2026, 4, 10),
        deductee_type=TDSDeducteeType.INDIVIDUAL,
        has_pan=True,
    )
    assert result.tds_applicable is False
    assert result.reason == "BELOW_THRESHOLD"


@pytest.mark.asyncio
async def test_194j_single_threshold_30k(service: TDSEntryService) -> None:
    """194J (professional fees): single threshold ₹30,000."""
    section = _section(
        code="194J",
        threshold_single=Decimal("30000"),
        rate_individual=Decimal("10.00"),
        rate_company=Decimal("10.00"),
    )
    service.section_repo.get = AsyncMock(return_value=section)
    result = await service.validate_threshold(
        organization_id=ORG_ID,
        vendor_id=None,
        tds_section_id=section.id,
        base_amount=Decimal("50000"),
        deduction_date=date(2026, 5, 1),
        deductee_type=TDSDeducteeType.INDIVIDUAL,
        has_pan=True,
    )
    assert result.tds_applicable is True
    assert result.reason == "SINGLE_THRESHOLD"
    # TDS rate picks up 10%: 50000 * 10% = 5000
    assert result.tds_rate == Decimal("10.00")
    assert result.estimated_tds == Decimal("5000.00")


# ---------------------------------------------------------------------------
# Annual-aggregate threshold.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_annual_aggregate_crosses_on_new_payment(service: TDSEntryService) -> None:
    """194C: annual threshold ₹1,00,000. Existing aggregate ₹80k + new ₹25k = ₹1.05L → crossed."""
    section = _section(
        code="194C",
        threshold_single=Decimal("30000"),
        threshold_annual=Decimal("100000"),
    )
    fy = SimpleNamespace(id=uuid4())
    service.section_repo.get = AsyncMock(return_value=section)
    service.repo.get_financial_year_for_date = AsyncMock(return_value=fy)
    service.repo.get_vendor_aggregate = AsyncMock(return_value=Decimal("80000"))

    result = await service.validate_threshold(
        organization_id=ORG_ID,
        vendor_id=uuid4(),
        tds_section_id=section.id,
        base_amount=Decimal("25000"),  # below SINGLE but pushes aggregate past ANNUAL
        deduction_date=date(2026, 10, 1),
        deductee_type=TDSDeducteeType.INDIVIDUAL,
        has_pan=True,
    )
    assert result.tds_applicable is True
    assert result.reason == "AGGREGATE_THRESHOLD"
    assert result.current_aggregate == Decimal("80000")
    assert result.new_aggregate == Decimal("105000")


@pytest.mark.asyncio
async def test_annual_aggregate_not_crossed_if_new_sum_still_below(
    service: TDSEntryService,
) -> None:
    """Existing ₹40k + new ₹20k = ₹60k — still below ₹1L annual."""
    section = _section(
        threshold_single=Decimal("30000"),
        threshold_annual=Decimal("100000"),
    )
    fy = SimpleNamespace(id=uuid4())
    service.section_repo.get = AsyncMock(return_value=section)
    service.repo.get_financial_year_for_date = AsyncMock(return_value=fy)
    service.repo.get_vendor_aggregate = AsyncMock(return_value=Decimal("40000"))

    result = await service.validate_threshold(
        organization_id=ORG_ID,
        vendor_id=uuid4(),
        tds_section_id=section.id,
        base_amount=Decimal("20000"),
        deduction_date=date(2026, 7, 1),
        deductee_type=TDSDeducteeType.INDIVIDUAL,
        has_pan=True,
    )
    assert result.tds_applicable is False
    assert result.reason == "BELOW_THRESHOLD"


# ---------------------------------------------------------------------------
# No threshold (both zero) = always applicable.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_zero_thresholds_means_always_applicable(service: TDSEntryService) -> None:
    """Sections like 195 (payments to non-residents) have no threshold — every rupee."""
    section = _section(
        code="195",
        threshold_single=Decimal("0"),
        threshold_annual=Decimal("0"),
        rate_individual=Decimal("20.00"),
        rate_company=Decimal("20.00"),
    )
    service.section_repo.get = AsyncMock(return_value=section)
    result = await service.validate_threshold(
        organization_id=ORG_ID,
        vendor_id=None,
        tds_section_id=section.id,
        base_amount=Decimal("1.00"),  # even ₹1
        deduction_date=date(2026, 4, 10),
        deductee_type=TDSDeducteeType.INDIVIDUAL,
        has_pan=True,
    )
    assert result.tds_applicable is True
    assert result.reason == "NO_THRESHOLD"


# ---------------------------------------------------------------------------
# Single-beats-annual precedence: both fire on the same row, SINGLE wins.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_single_threshold_wins_over_annual_when_both_crossed(
    service: TDSEntryService,
) -> None:
    """If a single payment both exceeds single-threshold and pushes aggregate past
    annual threshold, the service reports SINGLE_THRESHOLD (evaluated first)."""
    section = _section(
        threshold_single=Decimal("30000"),
        threshold_annual=Decimal("100000"),
    )
    fy = SimpleNamespace(id=uuid4())
    service.section_repo.get = AsyncMock(return_value=section)
    service.repo.get_financial_year_for_date = AsyncMock(return_value=fy)
    service.repo.get_vendor_aggregate = AsyncMock(return_value=Decimal("80000"))

    result = await service.validate_threshold(
        organization_id=ORG_ID,
        vendor_id=uuid4(),
        tds_section_id=section.id,
        base_amount=Decimal("50000"),  # > single AND pushes annual past
        deduction_date=date(2026, 10, 1),
        deductee_type=TDSDeducteeType.INDIVIDUAL,
        has_pan=True,
    )
    assert result.tds_applicable is True
    assert result.reason == "SINGLE_THRESHOLD"


# ---------------------------------------------------------------------------
# No-PAN 20% override compounds with threshold logic.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_pan_rate_20_percent_when_threshold_crossed(service: TDSEntryService) -> None:
    """§206AA: no-PAN vendor crossing 194C single threshold attracts 20% — not 1%."""
    section = _section(
        code="194C",
        threshold_single=Decimal("30000"),
        rate_individual=Decimal("1.00"),
        rate_no_pan=Decimal("20.00"),
    )
    service.section_repo.get = AsyncMock(return_value=section)
    result = await service.validate_threshold(
        organization_id=ORG_ID,
        vendor_id=None,
        tds_section_id=section.id,
        base_amount=Decimal("40000"),
        deduction_date=date(2026, 4, 10),
        deductee_type=TDSDeducteeType.INDIVIDUAL,
        has_pan=False,
    )
    assert result.tds_applicable is True
    assert result.reason == "SINGLE_THRESHOLD"
    assert result.tds_rate == Decimal("20.00")
    # 40,000 × 20% = 8,000
    assert result.estimated_tds == Decimal("8000.00")


# ---------------------------------------------------------------------------
# Cess is always applied on top of TDS + surcharge.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cess_applied_on_tds_plus_surcharge(service: TDSEntryService) -> None:
    """4% health + education cess on (TDS + surcharge). No surcharge here → cess on TDS."""
    section = _section(
        code="194J",
        threshold_single=Decimal("30000"),
        rate_individual=Decimal("10.00"),
        rate_company=Decimal("10.00"),
        cess_rate=Decimal("4.00"),
    )
    service.section_repo.get = AsyncMock(return_value=section)
    result = await service.validate_threshold(
        organization_id=ORG_ID,
        vendor_id=None,
        tds_section_id=section.id,
        base_amount=Decimal("100000"),
        deduction_date=date(2026, 4, 10),
        deductee_type=TDSDeducteeType.INDIVIDUAL,
        has_pan=True,
    )
    # TDS 10% of 1L = 10,000; cess 4% of 10k = 400. No surcharge.
    assert result.estimated_tds == Decimal("10000.00")
    assert result.estimated_surcharge == Decimal("0.00")
    assert result.estimated_cess == Decimal("400.00")
    assert result.estimated_total_tds == Decimal("10400.00")


# ---------------------------------------------------------------------------
# No-vendor path: aggregate lookup is skipped.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_vendor_skips_aggregate_lookup(service: TDSEntryService) -> None:
    """When vendor_id is None, aggregate stays 0 and only single-threshold matters."""
    section = _section(
        threshold_single=Decimal("30000"),
        threshold_annual=Decimal("100000"),
    )
    service.section_repo.get = AsyncMock(return_value=section)

    result = await service.validate_threshold(
        organization_id=ORG_ID,
        vendor_id=None,
        tds_section_id=section.id,
        base_amount=Decimal("5000"),  # below single, no annual because no vendor
        deduction_date=date(2026, 4, 10),
        deductee_type=TDSDeducteeType.INDIVIDUAL,
        has_pan=True,
    )
    assert result.tds_applicable is False
    assert result.current_aggregate == Decimal("0")
    assert result.new_aggregate == Decimal("5000")
    # Aggregate repo should NOT have been called.
    service.repo.get_vendor_aggregate.assert_not_awaited()
