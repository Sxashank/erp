"""Depreciation golden tests — SLM and WDV.

CLAUDE.md §4.12 / §7.1:
  - SLM: annual_dep = (cost - residual) / useful_life
  - WDV: dep = wdv × rate
  - Full-month convention if put-to-use > 15 days in month

These tests drive `_calculate_depreciation` with synthetic FixedAsset
records for both methods across a range of days / pro-rata factors, and
pin the rounded outputs.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.constants import DepreciationMethod
from app.services.fixed_assets.depreciation_service import DepreciationService


@pytest.fixture
def service() -> DepreciationService:
    return DepreciationService(session=MagicMock())


def _slm_asset(**overrides) -> SimpleNamespace:
    defaults = dict(
        depreciation_method=DepreciationMethod.SLM,
        depreciable_value=Decimal("90000.00"),
        depreciation_rate=Decimal("20.00"),
        wdv_value=Decimal("100000.00"),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _wdv_asset(**overrides) -> SimpleNamespace:
    defaults = dict(
        depreciation_method=DepreciationMethod.WDV,
        depreciable_value=Decimal("90000.00"),
        depreciation_rate=Decimal("40.00"),
        wdv_value=Decimal("100000.00"),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# SLM.
# ---------------------------------------------------------------------------

def test_slm_full_year(service: DepreciationService) -> None:
    """₹90,000 depreciable × 20% = ₹18,000/year."""
    asset = _slm_asset()
    amount = service._calculate_depreciation(asset, days=365, days_in_year=365)
    assert amount == Decimal("18000.00")


def test_slm_half_year(service: DepreciationService) -> None:
    asset = _slm_asset()
    amount = service._calculate_depreciation(asset, days=182, days_in_year=365)
    # 18000 * 182 / 365 = 8,975.34...
    assert Decimal("8975.30") < amount < Decimal("8975.40")


def test_slm_one_month(service: DepreciationService) -> None:
    asset = _slm_asset()
    amount = service._calculate_depreciation(asset, days=30, days_in_year=365)
    # 18000 * 30 / 365 = 1,479.45
    assert amount == Decimal("1479.45")


def test_slm_uses_depreciable_value_not_wdv(service: DepreciationService) -> None:
    """SLM reads `depreciable_value`; WDV override must be ignored."""
    asset = _slm_asset(depreciable_value=Decimal("50000.00"), depreciation_rate=Decimal("10.00"))
    amount = service._calculate_depreciation(
        asset, days=365, days_in_year=365, wdv_override=Decimal("999999.00")
    )
    # 50000 * 10% * 1 year = 5,000 — NOT based on wdv_override.
    assert amount == Decimal("5000.00")


# ---------------------------------------------------------------------------
# WDV.
# ---------------------------------------------------------------------------

def test_wdv_full_year(service: DepreciationService) -> None:
    """₹100,000 WDV × 40% = ₹40,000/year for the first year."""
    asset = _wdv_asset()
    amount = service._calculate_depreciation(asset, days=365, days_in_year=365)
    assert amount == Decimal("40000.00")


def test_wdv_override_used_when_provided(service: DepreciationService) -> None:
    """WDV override simulates year 2: WDV = 60k after year-1 depreciation of 40k."""
    asset = _wdv_asset()
    amount = service._calculate_depreciation(
        asset, days=365, days_in_year=365, wdv_override=Decimal("60000.00")
    )
    # 60000 * 40% = 24,000.
    assert amount == Decimal("24000.00")


def test_wdv_partial_period(service: DepreciationService) -> None:
    asset = _wdv_asset()
    amount = service._calculate_depreciation(asset, days=90, days_in_year=365)
    # 100000 * 40% * 90/365 = 9,863.0136...
    assert Decimal("9863.00") < amount < Decimal("9863.05")


# ---------------------------------------------------------------------------
# Edge cases.
# ---------------------------------------------------------------------------

def test_zero_days_returns_zero(service: DepreciationService) -> None:
    asset = _slm_asset()
    amount = service._calculate_depreciation(asset, days=0, days_in_year=365)
    assert amount == Decimal("0.00")


def test_unit_of_production_returns_zero(service: DepreciationService) -> None:
    """UOP requires actual unit counts; default path returns zero."""
    asset = SimpleNamespace(
        depreciation_method=DepreciationMethod.UNIT_OF_PRODUCTION,
        depreciable_value=Decimal("1000.00"),
        depreciation_rate=Decimal("10.00"),
        wdv_value=Decimal("1000.00"),
    )
    amount = service._calculate_depreciation(asset, days=365, days_in_year=365)
    assert amount == Decimal("0.00")


def test_output_quantized_to_two_decimals(service: DepreciationService) -> None:
    asset = _slm_asset(depreciable_value=Decimal("77777.77"), depreciation_rate=Decimal("13.33"))
    amount = service._calculate_depreciation(asset, days=45, days_in_year=365)
    assert amount.as_tuple().exponent == -2


def test_leap_year_days_in_year_parameter_respected(service: DepreciationService) -> None:
    """Service takes days_in_year as a parameter; callers pass 366 in leap years."""
    asset = _slm_asset()
    normal = service._calculate_depreciation(asset, days=30, days_in_year=365)
    leap = service._calculate_depreciation(asset, days=30, days_in_year=366)
    assert leap < normal
