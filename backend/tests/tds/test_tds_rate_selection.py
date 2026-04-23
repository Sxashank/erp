"""TDS rate-selection golden tests (STAGE-4-PENDING-005 closure).

Per Income Tax Act §206AA — deductee without PAN attracts the higher of:
  (a) the rate specified in the Act,
  (b) the rate in force, or
  (c) 20%.

These tests pin the rate-selection logic in `TDSEntryService._get_tds_rate`
+ surcharge calculation, across all major sections (194A/C/H/I/J + 195).
Pure-math, no DB.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.constants import TDSDeducteeType
from app.services.tds.tds_entry_service import TDSEntryService


@pytest.fixture
def service() -> TDSEntryService:
    return TDSEntryService(session=MagicMock())


def _section(
    *,
    code: str,
    rate_individual: Decimal,
    rate_company: Decimal,
    rate_no_pan: Decimal = Decimal("20.00"),
    threshold_single: Decimal = Decimal("0"),
    threshold_annual: Decimal = Decimal("0"),
    surcharge_applicable: bool = False,
    surcharge_slabs: list | None = None,
    cess_rate: Decimal = Decimal("4.00"),
) -> SimpleNamespace:
    return SimpleNamespace(
        code=code,
        rate_individual=rate_individual,
        rate_company=rate_company,
        rate_no_pan=rate_no_pan,
        threshold_single=threshold_single,
        threshold_annual=threshold_annual,
        surcharge_applicable=surcharge_applicable,
        surcharge_slabs=surcharge_slabs,
        cess_rate=cess_rate,
    )


# ---------------------------------------------------------------------------
# Rate selection per section, with + without PAN.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "section_code,rate_individual,rate_company",
    [
        ("194A", Decimal("10.00"), Decimal("10.00")),   # interest other than on securities
        ("194C", Decimal("1.00"), Decimal("2.00")),     # contractor payments
        ("194H", Decimal("5.00"), Decimal("5.00")),     # commission / brokerage
        ("194I_BUILDING", Decimal("10.00"), Decimal("10.00")),  # rent on land/building
        ("194I_PLANT", Decimal("2.00"), Decimal("2.00")),       # rent on plant & machinery
        ("194J", Decimal("10.00"), Decimal("10.00")),   # professional fees
        ("195", Decimal("20.00"), Decimal("20.00")),    # payment to non-residents
    ],
)
def test_rate_with_pan_individual(
    service: TDSEntryService,
    section_code: str,
    rate_individual: Decimal,
    rate_company: Decimal,
) -> None:
    section = _section(code=section_code, rate_individual=rate_individual, rate_company=rate_company)
    rate = service._get_tds_rate(section, TDSDeducteeType.INDIVIDUAL, has_pan=True)
    assert rate == rate_individual


@pytest.mark.parametrize(
    "section_code,rate_individual,rate_company",
    [
        ("194A", Decimal("10.00"), Decimal("10.00")),
        ("194C", Decimal("1.00"), Decimal("2.00")),
        ("194H", Decimal("5.00"), Decimal("5.00")),
        ("194J", Decimal("10.00"), Decimal("10.00")),
    ],
)
def test_rate_with_pan_company(
    service: TDSEntryService,
    section_code: str,
    rate_individual: Decimal,
    rate_company: Decimal,
) -> None:
    section = _section(code=section_code, rate_individual=rate_individual, rate_company=rate_company)
    rate = service._get_tds_rate(section, TDSDeducteeType.COMPANY, has_pan=True)
    assert rate == rate_company


@pytest.mark.parametrize(
    "section_code,rate_individual,rate_company",
    [
        ("194A", Decimal("10.00"), Decimal("10.00")),
        ("194C", Decimal("1.00"), Decimal("2.00")),
        ("194H", Decimal("5.00"), Decimal("5.00")),
        ("194J", Decimal("10.00"), Decimal("10.00")),
    ],
)
def test_no_pan_forces_20_percent_regardless_of_deductee(
    service: TDSEntryService,
    section_code: str,
    rate_individual: Decimal,
    rate_company: Decimal,
) -> None:
    """§206AA: no-PAN → 20% minimum, regardless of deductee type."""
    section = _section(
        code=section_code,
        rate_individual=rate_individual,
        rate_company=rate_company,
        rate_no_pan=Decimal("20.00"),
    )
    for deductee in (TDSDeducteeType.INDIVIDUAL, TDSDeducteeType.COMPANY):
        rate = service._get_tds_rate(section, deductee, has_pan=False)
        assert rate == Decimal("20.00")


def test_rate_company_vs_individual_different_for_194c(service: TDSEntryService) -> None:
    """194C splits 1% (individual/HUF) vs 2% (others) — confirm the split."""
    section = _section(
        code="194C",
        rate_individual=Decimal("1.00"),
        rate_company=Decimal("2.00"),
    )
    assert service._get_tds_rate(section, TDSDeducteeType.INDIVIDUAL, has_pan=True) == Decimal("1.00")
    assert service._get_tds_rate(section, TDSDeducteeType.COMPANY, has_pan=True) == Decimal("2.00")


# ---------------------------------------------------------------------------
# Surcharge slabs.
# ---------------------------------------------------------------------------

def test_surcharge_zero_when_not_applicable(service: TDSEntryService) -> None:
    section = _section(
        code="194A",
        rate_individual=Decimal("10.00"),
        rate_company=Decimal("10.00"),
        surcharge_applicable=False,
    )
    out = service._calculate_surcharge(
        tds_amount=Decimal("10000"),
        base_amount=Decimal("100000"),
        section=section,
        deductee_type=TDSDeducteeType.INDIVIDUAL,
    )
    assert out == Decimal("0.00")


def test_surcharge_zero_in_lowest_slab(service: TDSEntryService) -> None:
    """Individuals below ₹50L — 0% surcharge. Slab rates are fractions."""
    section = _section(
        code="195",
        rate_individual=Decimal("20.00"),
        rate_company=Decimal("20.00"),
        surcharge_applicable=True,
        surcharge_slabs=[
            {"min": 0, "max": 5000000, "rates": {"INDIVIDUAL": 0, "COMPANY": 0}},
            {"min": 5000000, "max": 10000000, "rates": {"INDIVIDUAL": 0.10, "COMPANY": 0.02}},
        ],
    )
    out = service._calculate_surcharge(
        tds_amount=Decimal("400000"),
        base_amount=Decimal("2000000"),  # ₹20L, below ₹50L
        section=section,
        deductee_type=TDSDeducteeType.INDIVIDUAL,
    )
    assert out == Decimal("0.00")


def test_surcharge_applies_in_50l_to_1cr_slab_individual(service: TDSEntryService) -> None:
    """Individuals in ₹50L–₹1Cr — 10% surcharge on TDS."""
    section = _section(
        code="195",
        rate_individual=Decimal("20.00"),
        rate_company=Decimal("20.00"),
        surcharge_applicable=True,
        surcharge_slabs=[
            {"min": 0, "max": 5000000, "rates": {"INDIVIDUAL": 0, "COMPANY": 0}},
            {"min": 5000000, "max": 10000000, "rates": {"INDIVIDUAL": 0.10, "COMPANY": 0.02}},
        ],
    )
    out = service._calculate_surcharge(
        tds_amount=Decimal("1500000"),
        base_amount=Decimal("7500000"),  # ₹75L
        section=section,
        deductee_type=TDSDeducteeType.INDIVIDUAL,
    )
    # 10% surcharge on ₹15L TDS = ₹1,50,000
    assert out == Decimal("150000.00")


def test_surcharge_rates_differ_by_deductee_type(service: TDSEntryService) -> None:
    section = _section(
        code="195",
        rate_individual=Decimal("20.00"),
        rate_company=Decimal("20.00"),
        surcharge_applicable=True,
        surcharge_slabs=[
            {"min": 5000000, "max": 10000000, "rates": {"INDIVIDUAL": 0.10, "COMPANY": 0.02}},
        ],
    )
    indiv = service._calculate_surcharge(
        tds_amount=Decimal("1000000"),
        base_amount=Decimal("7000000"),
        section=section,
        deductee_type=TDSDeducteeType.INDIVIDUAL,
    )
    company = service._calculate_surcharge(
        tds_amount=Decimal("1000000"),
        base_amount=Decimal("7000000"),
        section=section,
        deductee_type=TDSDeducteeType.COMPANY,
    )
    assert indiv == Decimal("100000.00")   # 10% of ₹10L
    assert company == Decimal("20000.00")  # 2% of ₹10L
