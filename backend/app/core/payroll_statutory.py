"""Payroll statutory computation helpers (STAGE-4-PENDING-007 closure).

CLAUDE.md §4.11 / §7.1:
  - PF: 12% on (Basic + DA) capped at ₹15,000; employer 3.67% + EPS 8.33% + admin 0.5%.
  - ESI: 0.75% employee, 3.25% employer; applicable if gross ≤ ₹21,000.
  - Professional Tax (PT): state-wise slabs (Maharashtra table encoded below).
  - Gratuity: (last drawn × 15 × years) / 26; cap ₹20,00,000; eligibility ≥ 5 years.
  - TDS regime: old vs new switchable; standard deduction ₹75,000 (new); 80C/80D in old only.
  - LOP: per-day prorated on gross; no statutory deductions on LOP days.

All helpers are pure, no DB. Imported by `PayrollService` when that service
finishes wiring. See STAGE-6-PENDING-payroll-batch.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

# -----------------------------------------------------------------------
# PF (EPF 1952).
# -----------------------------------------------------------------------

PF_WAGE_CEILING = Decimal("15000")
PF_EMPLOYEE_RATE = Decimal("0.12")          # 12%
PF_EMPLOYER_EPF_RATE = Decimal("0.0367")    # 3.67% → EPF
PF_EMPLOYER_EPS_RATE = Decimal("0.0833")    # 8.33% → EPS (pension)
PF_ADMIN_CHARGES_RATE = Decimal("0.005")    # 0.5% → admin

# -----------------------------------------------------------------------
# ESI Act 1948.
# -----------------------------------------------------------------------

ESI_GROSS_CEILING = Decimal("21000")
ESI_EMPLOYEE_RATE = Decimal("0.0075")       # 0.75%
ESI_EMPLOYER_RATE = Decimal("0.0325")       # 3.25%

# -----------------------------------------------------------------------
# Gratuity (Payment of Gratuity Act 1972).
# -----------------------------------------------------------------------

GRATUITY_MIN_ELIGIBLE_YEARS = Decimal("5")
GRATUITY_DAYS_PER_MONTH = Decimal("26")     # "15 days' wages for every completed year"
GRATUITY_CAP = Decimal("2000000")           # ₹20 lakh statutory ceiling

# -----------------------------------------------------------------------
# TDS regime (FY 2024-25 onward, new regime).
# -----------------------------------------------------------------------

NEW_REGIME_STANDARD_DEDUCTION = Decimal("75000")
OLD_REGIME_STANDARD_DEDUCTION = Decimal("50000")


def _q(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# -----------------------------------------------------------------------
# PF.
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class PFBreakdown:
    pf_wages: Decimal           # the capped (Basic + DA) amount used for the calculation
    employee_contribution: Decimal
    employer_epf: Decimal
    employer_eps: Decimal
    employer_admin: Decimal
    employer_total: Decimal


def compute_pf(basic_plus_da: Decimal) -> PFBreakdown:
    """PF contribution split per EPF 1952.

    The wage base is min(Basic+DA, ₹15,000). Both employee (12%) and
    employer (12% split into EPF 3.67% + EPS 8.33% + admin 0.5%)
    contribute on the same capped base.
    """
    if basic_plus_da < 0:
        raise ValueError("basic_plus_da must be non-negative")

    wages = min(basic_plus_da, PF_WAGE_CEILING)
    emp = _q(wages * PF_EMPLOYEE_RATE)
    er_epf = _q(wages * PF_EMPLOYER_EPF_RATE)
    er_eps = _q(wages * PF_EMPLOYER_EPS_RATE)
    er_admin = _q(wages * PF_ADMIN_CHARGES_RATE)
    return PFBreakdown(
        pf_wages=wages,
        employee_contribution=emp,
        employer_epf=er_epf,
        employer_eps=er_eps,
        employer_admin=er_admin,
        employer_total=er_epf + er_eps + er_admin,
    )


# -----------------------------------------------------------------------
# ESI.
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class ESIBreakdown:
    applicable: bool
    employee_contribution: Decimal
    employer_contribution: Decimal


def compute_esi(gross_monthly_wages: Decimal) -> ESIBreakdown:
    """ESI kicks in for employees earning gross ≤ ₹21,000/month.

    Note: once coverage starts in a half-year, it continues to the end of
    the half-year even if wages later cross the ceiling. That lifecycle
    rule is owned by the ESI coverage service; this helper only answers
    "given this month's gross, what's the contribution?".
    """
    if gross_monthly_wages < 0:
        raise ValueError("gross_monthly_wages must be non-negative")

    if gross_monthly_wages > ESI_GROSS_CEILING:
        return ESIBreakdown(
            applicable=False,
            employee_contribution=Decimal("0"),
            employer_contribution=Decimal("0"),
        )
    return ESIBreakdown(
        applicable=True,
        employee_contribution=_q(gross_monthly_wages * ESI_EMPLOYEE_RATE),
        employer_contribution=_q(gross_monthly_wages * ESI_EMPLOYER_RATE),
    )


# -----------------------------------------------------------------------
# Professional Tax (Maharashtra slab shown; other states extend this dict).
# -----------------------------------------------------------------------

# Slab shape: list of (upper_bound_exclusive, monthly_amount). Last slab
# uses Decimal('inf') as the upper bound.
# Maharashtra FY 2024-25:
#   up to ₹7,500  →  ₹0
#   ₹7,501-10,000 → ₹175
#   above ₹10,000 → ₹200 (Feb: ₹300 in some states, ignore for now)
MAHARASHTRA_PT_SLABS: tuple[tuple[Decimal, Decimal], ...] = (
    (Decimal("7500.01"), Decimal("0")),
    (Decimal("10000.01"), Decimal("175")),
    (Decimal("Infinity"), Decimal("200")),
)


def compute_pt_maharashtra(monthly_gross: Decimal) -> Decimal:
    """Maharashtra professional tax for a given monthly gross."""
    if monthly_gross < 0:
        raise ValueError("monthly_gross must be non-negative")
    for upper, amount in MAHARASHTRA_PT_SLABS:
        if monthly_gross < upper:
            return amount
    return MAHARASHTRA_PT_SLABS[-1][1]  # unreachable; kept for type safety


# -----------------------------------------------------------------------
# Gratuity.
# -----------------------------------------------------------------------

def compute_gratuity(
    *,
    last_drawn_monthly_wages: Decimal,
    years_of_service: Decimal,
) -> Decimal:
    """Gratuity = (last drawn × 15 × completed years) / 26, capped at ₹20L.

    `years_of_service` must be at least 5 for eligibility. Fractional
    years ≥ 6 months count as a full year; the caller rounds before
    passing in. (Kept as Decimal so the caller can pass 4.99 and see the
    eligibility failure cleanly.)
    """
    if last_drawn_monthly_wages < 0:
        raise ValueError("last_drawn_monthly_wages must be non-negative")
    if years_of_service < 0:
        raise ValueError("years_of_service must be non-negative")
    if years_of_service < GRATUITY_MIN_ELIGIBLE_YEARS:
        return Decimal("0.00")

    raw = last_drawn_monthly_wages * Decimal("15") * years_of_service / GRATUITY_DAYS_PER_MONTH
    return _q(min(raw, GRATUITY_CAP))


# -----------------------------------------------------------------------
# LOP proration.
# -----------------------------------------------------------------------

def compute_lop_deduction(
    *,
    gross_monthly_wages: Decimal,
    days_in_month: int,
    lop_days: Decimal,
) -> Decimal:
    """LOP deduction = (gross / days_in_month) × lop_days.

    Statutory contributions (PF/ESI) on LOP days do NOT accrue; the caller
    computes PF/ESI on the prorated (net-of-LOP) wage base.
    """
    if days_in_month <= 0:
        raise ValueError("days_in_month must be positive")
    if lop_days < 0:
        raise ValueError("lop_days must be non-negative")
    if lop_days > days_in_month:
        raise ValueError("lop_days cannot exceed days_in_month")
    per_day = gross_monthly_wages / Decimal(days_in_month)
    return _q(per_day * lop_days)


# -----------------------------------------------------------------------
# TDS — old vs new regime.
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class TDSRegimeResult:
    regime: str
    taxable_income: Decimal
    standard_deduction_applied: Decimal
    chapter_via_deductions_applied: Decimal


def apply_regime_deductions(
    *,
    gross_annual_income: Decimal,
    regime: str,
    chapter_via_deductions: Decimal = Decimal("0"),
) -> TDSRegimeResult:
    """Apply standard deduction + (old-regime-only) 80C/80D etc. deductions.

    Args:
      gross_annual_income:     sum of salary-head gross.
      regime:                  'old' or 'new'.
      chapter_via_deductions:  total 80C + 80D + ... (ignored in new regime).
    """
    r = regime.strip().lower()
    if r not in {"old", "new"}:
        raise ValueError(f"regime must be 'old' or 'new', got {regime!r}")
    if gross_annual_income < 0:
        raise ValueError("gross_annual_income must be non-negative")
    if chapter_via_deductions < 0:
        raise ValueError("chapter_via_deductions must be non-negative")

    std = NEW_REGIME_STANDARD_DEDUCTION if r == "new" else OLD_REGIME_STANDARD_DEDUCTION
    via = Decimal("0") if r == "new" else chapter_via_deductions
    taxable = max(Decimal("0"), gross_annual_income - std - via)
    return TDSRegimeResult(
        regime=r,
        taxable_income=_q(taxable),
        standard_deduction_applied=std,
        chapter_via_deductions_applied=via,
    )
