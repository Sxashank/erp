"""TDS challan number helpers — internal reference generation + bank CIN validation.

Two distinct identifiers are involved in TDS challan payments:

  * **Internal reference** — what *we* assign to a challan before paying it, so the
    deductor can track it internally. Format (NBFC-local convention):
        ``<TAN>/<FYCOMPACT>-<Q>/<SECTION>/<SEQ>``
    e.g. ``DELT12345A/2526-Q1/194C/00001``.

  * **Bank CIN (Challan Identification Number)** — the 20-digit identifier the
    bank returns on successful payment, per the OLTAS scheme:
        ``<BSR(7)><DDMMYYYY(8)><SERIAL(5)>``

This module is DB-free so it's unit-testable as pure math.
"""

from __future__ import annotations

from datetime import date
from typing import Final

_TAN_LEN: Final[int] = 10  # 4 letters + 5 digits + 1 letter; we pattern-check loosely
_BSR_LEN: Final[int] = 7
_SERIAL_LEN: Final[int] = 5
_CIN_LEN: Final[int] = _BSR_LEN + 8 + _SERIAL_LEN  # 20


def fiscal_year_for_date(d: date) -> str:
    """Return the Indian FY string ``YYYY-YY`` for the given date (FY starts 1 April)."""
    start_year = d.year if d.month >= 4 else d.year - 1
    end_yy = (start_year + 1) % 100
    return f"{start_year}-{end_yy:02d}"


def fiscal_quarter_for_date(d: date) -> str:
    """Return Q1 / Q2 / Q3 / Q4 per Indian FY for the given date."""
    m = d.month
    if 4 <= m <= 6:
        return "Q1"
    if 7 <= m <= 9:
        return "Q2"
    if 10 <= m <= 12:
        return "Q3"
    return "Q4"


def generate_internal_challan_number(
    *,
    deductor_tan: str,
    section_code: str,
    period_to: date,
    sequence: int,
) -> str:
    """Build an internal challan reference.

    Args:
        deductor_tan: The deductor's TAN (e.g. ``DELT12345A``). Required.
        section_code: TDS section short code (e.g. ``194C``). Required.
        period_to: End date of the aggregation window — used to derive FY and quarter.
        sequence: 1-based counter per (TAN, FY, Q, section). Zero-padded to 5 digits.

    Returns:
        ``<TAN>/<FYCOMPACT>-<Q>/<SECTION>/<SEQ>`` — e.g. ``DELT12345A/2526-Q1/194C/00001``.

    Raises:
        ValueError: if any input is empty or the sequence is < 1.
    """
    if not deductor_tan or not deductor_tan.strip():
        raise ValueError("deductor_tan is required")
    if not section_code or not section_code.strip():
        raise ValueError("section_code is required")
    if sequence < 1:
        raise ValueError("sequence must be >= 1")

    fy = fiscal_year_for_date(period_to)  # "2025-26"
    start_yy = fy.split("-")[0][-2:]
    end_yy = fy.split("-")[1]
    fy_compact = f"{start_yy}{end_yy}"  # "2526"

    return (
        f"{deductor_tan.strip().upper()}"
        f"/{fy_compact}-{fiscal_quarter_for_date(period_to)}"
        f"/{section_code.strip().upper()}"
        f"/{sequence:05d}"
    )


def build_bank_cin(*, bsr_code: str, payment_date: date, serial_number: str) -> str:
    """Build an OLTAS CIN from its three parts.

    Args:
        bsr_code: 7-digit bank branch code.
        payment_date: Tax payment date.
        serial_number: Bank-assigned serial, up to 5 digits. Zero-padded.

    Returns:
        20-char CIN ``<BSR><DDMMYYYY><SERIAL>``.

    Raises:
        ValueError: if BSR isn't 7 digits, serial isn't 1–5 digits, or any input is blank.
    """
    bsr = (bsr_code or "").strip()
    if len(bsr) != _BSR_LEN or not bsr.isdigit():
        raise ValueError(f"bsr_code must be {_BSR_LEN} digits")

    serial = (serial_number or "").strip()
    if not serial or not serial.isdigit() or len(serial) > _SERIAL_LEN:
        raise ValueError(f"serial_number must be 1..{_SERIAL_LEN} digits")

    date_part = payment_date.strftime("%d%m%Y")
    serial_padded = serial.zfill(_SERIAL_LEN)
    return f"{bsr}{date_part}{serial_padded}"


def validate_bank_cin(cin: str) -> bool:
    """Structural validity of an OLTAS CIN.

    Checks: length = 20, all-digits, and embedded DDMMYYYY parses as a real date.
    Returns True iff the CIN is well-formed; does NOT check that the BSR actually
    exists (that's an OLTAS round-trip) or that the serial hasn't been reused.
    """
    if not cin or len(cin) != _CIN_LEN or not cin.isdigit():
        return False
    d_part = cin[_BSR_LEN : _BSR_LEN + 8]
    try:
        date(int(d_part[4:8]), int(d_part[2:4]), int(d_part[0:2]))
    except ValueError:
        return False
    return True
