"""Payroll statutory golden tests (STAGE-4-PENDING-007 closure).

Covers PF cap, ESI eligibility, Professional Tax slabs, gratuity formula
+ statutory ceiling, LOP proration, TDS old-vs-new regime. See CLAUDE.md §4.11.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.core.payroll_statutory import (
    ESI_EMPLOYEE_RATE,
    ESI_EMPLOYER_RATE,
    ESI_GROSS_CEILING,
    GRATUITY_CAP,
    GRATUITY_MIN_ELIGIBLE_YEARS,
    NEW_REGIME_STANDARD_DEDUCTION,
    OLD_REGIME_STANDARD_DEDUCTION,
    PF_ADMIN_CHARGES_RATE,
    PF_EMPLOYEE_RATE,
    PF_EMPLOYER_EPF_RATE,
    PF_EMPLOYER_EPS_RATE,
    PF_WAGE_CEILING,
    apply_regime_deductions,
    compute_esi,
    compute_gratuity,
    compute_lop_deduction,
    compute_pf,
    compute_pt_maharashtra,
)


# ---------------------------------------------------------------------------
# PF constants + cap.
# ---------------------------------------------------------------------------

def test_pf_constants_match_epf_act() -> None:
    assert PF_WAGE_CEILING == Decimal("15000")
    assert PF_EMPLOYEE_RATE == Decimal("0.12")
    assert PF_EMPLOYER_EPF_RATE == Decimal("0.0367")
    assert PF_EMPLOYER_EPS_RATE == Decimal("0.0833")
    assert PF_ADMIN_CHARGES_RATE == Decimal("0.005")


def test_pf_below_ceiling_uses_actual_wages() -> None:
    """Basic+DA = ₹12,000 → employee PF = 12% × 12,000 = ₹1,440."""
    b = compute_pf(Decimal("12000"))
    assert b.pf_wages == Decimal("12000")
    assert b.employee_contribution == Decimal("1440.00")
    assert b.employer_epf == Decimal("440.40")    # 3.67%
    assert b.employer_eps == Decimal("999.60")    # 8.33%
    assert b.employer_admin == Decimal("60.00")   # 0.5%


def test_pf_at_ceiling_exactly() -> None:
    b = compute_pf(Decimal("15000"))
    assert b.pf_wages == Decimal("15000")
    assert b.employee_contribution == Decimal("1800.00")
    assert b.employer_epf == Decimal("550.50")
    assert b.employer_eps == Decimal("1249.50")


def test_pf_above_ceiling_capped() -> None:
    """Basic+DA = ₹30,000 → PF still computed on ₹15,000 cap."""
    b = compute_pf(Decimal("30000"))
    assert b.pf_wages == Decimal("15000")
    assert b.employee_contribution == Decimal("1800.00")


def test_pf_zero_wages_yields_zero() -> None:
    b = compute_pf(Decimal("0"))
    assert b.pf_wages == Decimal("0")
    assert b.employee_contribution == Decimal("0.00")
    assert b.employer_total == Decimal("0.00")


def test_pf_negative_wages_rejected() -> None:
    with pytest.raises(ValueError):
        compute_pf(Decimal("-1"))


# ---------------------------------------------------------------------------
# ESI.
# ---------------------------------------------------------------------------

def test_esi_constants() -> None:
    assert ESI_GROSS_CEILING == Decimal("21000")
    assert ESI_EMPLOYEE_RATE == Decimal("0.0075")
    assert ESI_EMPLOYER_RATE == Decimal("0.0325")


def test_esi_at_or_below_ceiling_is_applicable() -> None:
    b = compute_esi(Decimal("20000"))
    assert b.applicable is True
    assert b.employee_contribution == Decimal("150.00")
    assert b.employer_contribution == Decimal("650.00")


def test_esi_exact_ceiling_is_applicable() -> None:
    b = compute_esi(Decimal("21000"))
    assert b.applicable is True
    assert b.employee_contribution == Decimal("157.50")
    assert b.employer_contribution == Decimal("682.50")


def test_esi_above_ceiling_is_not_applicable() -> None:
    b = compute_esi(Decimal("21001"))
    assert b.applicable is False
    assert b.employee_contribution == Decimal("0")
    assert b.employer_contribution == Decimal("0")


def test_esi_zero_wages() -> None:
    b = compute_esi(Decimal("0"))
    assert b.applicable is True
    assert b.employee_contribution == Decimal("0.00")


# ---------------------------------------------------------------------------
# Professional Tax (Maharashtra).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "gross,expected_pt",
    [
        (Decimal("5000"), Decimal("0")),
        (Decimal("7500"), Decimal("0")),       # exactly at ₹7,500 → nil
        (Decimal("7501"), Decimal("175")),     # first paisa above → ₹175
        (Decimal("8000"), Decimal("175")),
        (Decimal("9999.99"), Decimal("175")),
        (Decimal("10000"), Decimal("175")),    # exactly at ₹10,000 → still ₹175
        (Decimal("10000.01"), Decimal("200")),  # above ₹10,000 → ₹200
        (Decimal("50000"), Decimal("200")),
        (Decimal("500000"), Decimal("200")),
    ],
)
def test_pt_maharashtra_slab(gross: Decimal, expected_pt: Decimal) -> None:
    assert compute_pt_maharashtra(gross) == expected_pt


def test_pt_maharashtra_negative_rejected() -> None:
    with pytest.raises(ValueError):
        compute_pt_maharashtra(Decimal("-1"))


# ---------------------------------------------------------------------------
# Gratuity.
# ---------------------------------------------------------------------------

def test_gratuity_constants() -> None:
    assert GRATUITY_CAP == Decimal("2000000")
    assert GRATUITY_MIN_ELIGIBLE_YEARS == Decimal("5")


def test_gratuity_under_5_years_is_zero() -> None:
    assert compute_gratuity(
        last_drawn_monthly_wages=Decimal("50000"),
        years_of_service=Decimal("4"),
    ) == Decimal("0.00")
    assert compute_gratuity(
        last_drawn_monthly_wages=Decimal("50000"),
        years_of_service=Decimal("4.99"),
    ) == Decimal("0.00")


def test_gratuity_exactly_5_years() -> None:
    """₹50,000 × 15 × 5 / 26 = ₹144,230.77"""
    out = compute_gratuity(
        last_drawn_monthly_wages=Decimal("50000"),
        years_of_service=Decimal("5"),
    )
    assert out == Decimal("144230.77")


def test_gratuity_standard_case_10_years() -> None:
    """₹75,000 × 15 × 10 / 26 = ₹432,692.31"""
    out = compute_gratuity(
        last_drawn_monthly_wages=Decimal("75000"),
        years_of_service=Decimal("10"),
    )
    assert out == Decimal("432692.31")


def test_gratuity_hits_20l_cap() -> None:
    """₹200,000 × 15 × 30 / 26 = ₹3,461,538 — capped at ₹20,00,000."""
    out = compute_gratuity(
        last_drawn_monthly_wages=Decimal("200000"),
        years_of_service=Decimal("30"),
    )
    assert out == Decimal("2000000.00")


def test_gratuity_zero_wages() -> None:
    assert compute_gratuity(
        last_drawn_monthly_wages=Decimal("0"),
        years_of_service=Decimal("10"),
    ) == Decimal("0.00")


def test_gratuity_negative_rejected() -> None:
    with pytest.raises(ValueError):
        compute_gratuity(last_drawn_monthly_wages=Decimal("-1"), years_of_service=Decimal("5"))
    with pytest.raises(ValueError):
        compute_gratuity(last_drawn_monthly_wages=Decimal("100"), years_of_service=Decimal("-1"))


# ---------------------------------------------------------------------------
# LOP proration.
# ---------------------------------------------------------------------------

def test_lop_zero_days_yields_zero_deduction() -> None:
    assert compute_lop_deduction(
        gross_monthly_wages=Decimal("30000"),
        days_in_month=30,
        lop_days=Decimal("0"),
    ) == Decimal("0.00")


def test_lop_one_day_proration_on_30_day_month() -> None:
    """₹30,000 / 30 = ₹1,000/day."""
    assert compute_lop_deduction(
        gross_monthly_wages=Decimal("30000"),
        days_in_month=30,
        lop_days=Decimal("1"),
    ) == Decimal("1000.00")


def test_lop_half_month() -> None:
    assert compute_lop_deduction(
        gross_monthly_wages=Decimal("30000"),
        days_in_month=30,
        lop_days=Decimal("15"),
    ) == Decimal("15000.00")


def test_lop_full_month_yields_full_gross() -> None:
    assert compute_lop_deduction(
        gross_monthly_wages=Decimal("30000"),
        days_in_month=30,
        lop_days=Decimal("30"),
    ) == Decimal("30000.00")


def test_lop_rejects_more_days_than_month() -> None:
    with pytest.raises(ValueError, match="cannot exceed"):
        compute_lop_deduction(
            gross_monthly_wages=Decimal("30000"),
            days_in_month=30,
            lop_days=Decimal("31"),
        )


def test_lop_rejects_negative_days() -> None:
    with pytest.raises(ValueError):
        compute_lop_deduction(
            gross_monthly_wages=Decimal("30000"),
            days_in_month=30,
            lop_days=Decimal("-1"),
        )


def test_lop_rejects_zero_days_in_month() -> None:
    with pytest.raises(ValueError):
        compute_lop_deduction(
            gross_monthly_wages=Decimal("30000"),
            days_in_month=0,
            lop_days=Decimal("0"),
        )


# ---------------------------------------------------------------------------
# TDS regime — standard deduction + 80C/80D.
# ---------------------------------------------------------------------------

def test_new_regime_standard_deduction_75k() -> None:
    assert NEW_REGIME_STANDARD_DEDUCTION == Decimal("75000")
    assert OLD_REGIME_STANDARD_DEDUCTION == Decimal("50000")


def test_new_regime_ignores_chapter_via_deductions() -> None:
    out = apply_regime_deductions(
        gross_annual_income=Decimal("1000000"),
        regime="new",
        chapter_via_deductions=Decimal("150000"),  # 80C claim — ignored
    )
    # Taxable = 10,00,000 − 75,000 = 9,25,000 (80C NOT applied)
    assert out.taxable_income == Decimal("925000.00")
    assert out.chapter_via_deductions_applied == Decimal("0")


def test_old_regime_applies_chapter_via_deductions() -> None:
    out = apply_regime_deductions(
        gross_annual_income=Decimal("1000000"),
        regime="old",
        chapter_via_deductions=Decimal("150000"),
    )
    # Taxable = 10,00,000 − 50,000 − 1,50,000 = 8,00,000
    assert out.taxable_income == Decimal("800000.00")


def test_regime_taxable_income_never_negative() -> None:
    """Deductions exceed income → clamped to zero, not negative."""
    out = apply_regime_deductions(
        gross_annual_income=Decimal("50000"),
        regime="new",
        chapter_via_deductions=Decimal("0"),
    )
    assert out.taxable_income == Decimal("0.00")


def test_regime_rejects_invalid_choice() -> None:
    with pytest.raises(ValueError, match="old.+new"):
        apply_regime_deductions(
            gross_annual_income=Decimal("100000"),
            regime="newest",
        )


def test_regime_accepts_uppercase() -> None:
    out = apply_regime_deductions(
        gross_annual_income=Decimal("200000"),
        regime="NEW",
    )
    assert out.regime == "new"
