"""EMI calculation golden tests.

Formula (CLAUDE.md §4.8 / §7.1):
    EMI = P · r · (1+r)ⁿ / ((1+r)ⁿ − 1)
    where r = monthly_rate = annual_rate / 12 / 100
          n = tenure in months
          P = principal

Monthly-compounded EMI is invariant to day-count conventions (ACT/365 etc.);
day-count only affects per-day interest accrual between payment dates, not
the EMI amount itself. These tests lock down the rounded EMI for every
scenario on the bank's test card.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.lending.loan_account_service import LoanAccountService


@pytest.fixture
def service() -> LoanAccountService:
    """_calculate_emi is instance method but pure — any service works."""
    return LoanAccountService(db=MagicMock())


# ---------------------------------------------------------------------------
# Zero-interest loans.
# ---------------------------------------------------------------------------

def test_zero_interest_splits_principal_evenly(service: LoanAccountService) -> None:
    # ₹12,000 over 12 months at 0% = ₹1,000/month exactly.
    emi = service._calculate_emi(Decimal("12000"), Decimal("0"), 12)
    assert emi == Decimal("1000.00")


def test_zero_interest_rounds_fractional_principal(service: LoanAccountService) -> None:
    # ₹1,000 / 3 months at 0% = ₹333.33/month.
    emi = service._calculate_emi(Decimal("1000"), Decimal("0"), 3)
    assert emi == Decimal("333.33")


# ---------------------------------------------------------------------------
# Standard amortising EMI — values cross-checked with a calculator.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "principal,rate,tenure,expected",
    [
        # Benchmark: RBI's standard housing loan example — ₹1 Cr, 9% p.a., 20 yrs.
        (Decimal("10000000"), Decimal("9.00"), 240, Decimal("89972.61")),
        # Small short-term loan: ₹1L at 12% for 12 months → ~₹8,885/month.
        (Decimal("100000"), Decimal("12.00"), 12, Decimal("8884.88")),
        # Medium tenure: ₹5L at 10.5% for 60 months.
        (Decimal("500000"), Decimal("10.50"), 60, Decimal("10746.95")),
        # Long tenure: ₹25L at 8.5% for 30 years.
        (Decimal("2500000"), Decimal("8.50"), 360, Decimal("19222.89")),
        # High-rate personal loan: ₹3L at 18% for 36 months.
        (Decimal("300000"), Decimal("18.00"), 36, Decimal("10845.72")),
        # NBFC MSME: ₹15L at 14% for 84 months (7 yrs).
        (Decimal("1500000"), Decimal("14.00"), 84, Decimal("28110.02")),
    ],
)
def test_emi_for_benchmark_loans(
    service: LoanAccountService,
    principal: Decimal,
    rate: Decimal,
    tenure: int,
    expected: Decimal,
) -> None:
    emi = service._calculate_emi(principal, rate, tenure)
    # Allow a 5-paise tolerance for rounding differences between calculator
    # sources; the formula rounds to 2 decimal places.
    assert abs(emi - expected) <= Decimal("0.05"), f"emi={emi}, expected~{expected}"


# ---------------------------------------------------------------------------
# Boundary tenures.
# ---------------------------------------------------------------------------

def test_single_month_emi_equals_principal_plus_interest(service: LoanAccountService) -> None:
    # ₹1L at 12% for 1 month: r=0.01 → EMI ≈ 100*1.01/1 → 101,000 (rounded).
    emi = service._calculate_emi(Decimal("100000"), Decimal("12.00"), 1)
    assert emi == Decimal("101000.00")


def test_very_long_tenure_converges(service: LoanAccountService) -> None:
    # 50 years = 600 months at 8%: EMI should converge near i*P as n→∞.
    emi = service._calculate_emi(Decimal("1000000"), Decimal("8.00"), 600)
    # Principal × monthly-rate = 1,000,000 * 0.00667 ≈ 6,667 (asymptote).
    assert emi > Decimal("6666.00") and emi < Decimal("6900.00")


# ---------------------------------------------------------------------------
# Rounding invariant.
# ---------------------------------------------------------------------------

def test_emi_is_rounded_to_two_decimals(service: LoanAccountService) -> None:
    emi = service._calculate_emi(Decimal("123456.78"), Decimal("11.25"), 48)
    # Check the quantize contract holds.
    assert emi.as_tuple().exponent == -2


# ---------------------------------------------------------------------------
# Monotonicity: EMI increases with rate (for same P, n).
# ---------------------------------------------------------------------------

def test_emi_monotonic_in_rate(service: LoanAccountService) -> None:
    base = service._calculate_emi(Decimal("1000000"), Decimal("8.00"), 120)
    higher = service._calculate_emi(Decimal("1000000"), Decimal("12.00"), 120)
    assert higher > base


def test_emi_monotonic_in_principal(service: LoanAccountService) -> None:
    small = service._calculate_emi(Decimal("500000"), Decimal("10.00"), 60)
    large = service._calculate_emi(Decimal("1000000"), Decimal("10.00"), 60)
    assert large > small


def test_emi_decreasing_in_tenure(service: LoanAccountService) -> None:
    short = service._calculate_emi(Decimal("1000000"), Decimal("10.00"), 24)
    long_ = service._calculate_emi(Decimal("1000000"), Decimal("10.00"), 120)
    assert long_ < short
