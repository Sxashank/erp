"""TDS challan numbering tests (STAGE-4-PENDING-005b).

Covers:
  * Internal reference format (``TAN/FY-Q/SECTION/SEQ``) + derived FY/quarter.
  * OLTAS CIN builder (``BSR + DDMMYYYY + SERIAL``) and validator.

Pure math — no DB.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.core.tds_challan_number import (
    build_bank_cin,
    fiscal_quarter_for_date,
    fiscal_year_for_date,
    generate_internal_challan_number,
    validate_bank_cin,
)

# ---------------------------------------------------------------------------
# Fiscal-year / quarter helpers.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "d,fy",
    [
        (date(2025, 4, 1), "2025-26"),  # FY start
        (date(2025, 3, 31), "2024-25"),  # day before FY start → previous FY
        (date(2026, 1, 15), "2025-26"),  # Jan still belongs to prior-year FY
        (date(2026, 3, 31), "2025-26"),  # FY end
        (date(2026, 4, 1), "2026-27"),  # next FY start
    ],
)
def test_fiscal_year_for_date(d: date, fy: str) -> None:
    assert fiscal_year_for_date(d) == fy


@pytest.mark.parametrize(
    "d,q",
    [
        (date(2025, 4, 1), "Q1"),
        (date(2025, 6, 30), "Q1"),
        (date(2025, 7, 1), "Q2"),
        (date(2025, 9, 30), "Q2"),
        (date(2025, 10, 1), "Q3"),
        (date(2025, 12, 31), "Q3"),
        (date(2026, 1, 1), "Q4"),
        (date(2026, 3, 31), "Q4"),
    ],
)
def test_fiscal_quarter_for_date(d: date, q: str) -> None:
    assert fiscal_quarter_for_date(d) == q


# ---------------------------------------------------------------------------
# Internal challan reference generation.
# ---------------------------------------------------------------------------


def test_generate_internal_challan_number_happy_path() -> None:
    ref = generate_internal_challan_number(
        deductor_tan="DELT12345A",
        section_code="194C",
        period_to=date(2025, 6, 30),
        sequence=1,
    )
    assert ref == "DELT12345A/2526-Q1/194C/00001"


def test_generate_internal_challan_number_uppercases_tan_and_section() -> None:
    """Caller sloppiness tolerated — TAN and section are uppercased."""
    ref = generate_internal_challan_number(
        deductor_tan=" delt12345a ",
        section_code=" 194c ",
        period_to=date(2025, 6, 30),
        sequence=1,
    )
    assert ref == "DELT12345A/2526-Q1/194C/00001"


def test_generate_internal_challan_number_pads_sequence() -> None:
    ref = generate_internal_challan_number(
        deductor_tan="DELT12345A",
        section_code="194J",
        period_to=date(2025, 9, 30),
        sequence=42,
    )
    assert ref == "DELT12345A/2526-Q2/194J/00042"


def test_generate_internal_challan_number_sequence_five_digits_still_padded() -> None:
    ref = generate_internal_challan_number(
        deductor_tan="DELT12345A",
        section_code="194J",
        period_to=date(2025, 9, 30),
        sequence=99999,
    )
    assert ref.endswith("/99999")


def test_generate_internal_challan_number_q4_uses_ending_fy() -> None:
    """Jan-Mar falls in Q4 of the FY that started the previous April."""
    ref = generate_internal_challan_number(
        deductor_tan="DELT12345A",
        section_code="194C",
        period_to=date(2026, 1, 31),
        sequence=1,
    )
    assert "/2526-Q4/" in ref


@pytest.mark.parametrize(
    "bad_tan",
    ["", "   ", None],
)
def test_generate_internal_challan_number_rejects_blank_tan(bad_tan) -> None:
    with pytest.raises(ValueError, match="deductor_tan"):
        generate_internal_challan_number(
            deductor_tan=bad_tan,  # type: ignore[arg-type]
            section_code="194C",
            period_to=date(2025, 6, 30),
            sequence=1,
        )


def test_generate_internal_challan_number_rejects_blank_section() -> None:
    with pytest.raises(ValueError, match="section_code"):
        generate_internal_challan_number(
            deductor_tan="DELT12345A",
            section_code="",
            period_to=date(2025, 6, 30),
            sequence=1,
        )


def test_generate_internal_challan_number_rejects_zero_sequence() -> None:
    with pytest.raises(ValueError, match="sequence"):
        generate_internal_challan_number(
            deductor_tan="DELT12345A",
            section_code="194C",
            period_to=date(2025, 6, 30),
            sequence=0,
        )


# ---------------------------------------------------------------------------
# OLTAS CIN builder.
# ---------------------------------------------------------------------------


def test_build_bank_cin_happy_path() -> None:
    cin = build_bank_cin(
        bsr_code="0510308",
        payment_date=date(2025, 6, 7),
        serial_number="12345",
    )
    assert cin == "0510308" "07062025" "12345"
    assert len(cin) == 20


def test_build_bank_cin_pads_short_serial() -> None:
    cin = build_bank_cin(
        bsr_code="0510308",
        payment_date=date(2025, 6, 7),
        serial_number="42",
    )
    assert cin.endswith("00042")
    assert len(cin) == 20


@pytest.mark.parametrize(
    "bsr",
    [
        "",  # blank
        "051030",  # 6 digits
        "05103088",  # 8 digits
        "ABCDEFG",  # non-numeric
    ],
)
def test_build_bank_cin_rejects_bad_bsr(bsr: str) -> None:
    with pytest.raises(ValueError, match="bsr_code"):
        build_bank_cin(bsr_code=bsr, payment_date=date(2025, 6, 7), serial_number="1")


@pytest.mark.parametrize(
    "serial",
    [
        "",
        "123456",  # 6 digits
        "AB12",
    ],
)
def test_build_bank_cin_rejects_bad_serial(serial: str) -> None:
    with pytest.raises(ValueError, match="serial_number"):
        build_bank_cin(
            bsr_code="0510308",
            payment_date=date(2025, 6, 7),
            serial_number=serial,
        )


# ---------------------------------------------------------------------------
# OLTAS CIN validator.
# ---------------------------------------------------------------------------


def test_validate_bank_cin_accepts_well_formed() -> None:
    assert validate_bank_cin("05103080706202512345")


def test_validate_bank_cin_rejects_wrong_length() -> None:
    assert not validate_bank_cin("123")
    assert not validate_bank_cin("1" * 19)
    assert not validate_bank_cin("1" * 21)


def test_validate_bank_cin_rejects_non_numeric() -> None:
    assert not validate_bank_cin("A" * 20)
    # letter buried inside otherwise-valid digits
    assert not validate_bank_cin("05103080706202512A45")


def test_validate_bank_cin_rejects_bad_embedded_date() -> None:
    # Day=32 for june → not a real date
    bad = "0510308" "32062025" "12345"
    assert len(bad) == 20
    assert not validate_bank_cin(bad)


def test_validate_bank_cin_rejects_empty_or_none() -> None:
    assert not validate_bank_cin("")
    # mypy: validator accepts Optional-like input; None path asserted
    assert not validate_bank_cin(None)  # type: ignore[arg-type]


def test_builder_output_round_trips_through_validator() -> None:
    """Any CIN the builder accepts should pass the validator."""
    cin = build_bank_cin(
        bsr_code="0510308",
        payment_date=date(2025, 6, 7),
        serial_number="12345",
    )
    assert validate_bank_cin(cin)
