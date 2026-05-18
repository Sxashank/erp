"""LDC (Lower Deduction Certificate) rate-selection golden tests (STAGE-4-PENDING-005b).

§197 of the IT Act permits an AO to issue a certificate allowing TDS at a rate
below the default. The cert has a validity window and (optionally) a cap.

Precedence (highest first):
  1. §206AA (no PAN → 20%) — always wins, LDC never overrides this
  2. Valid in-window, limit-covered LDC → LDC rate
  3. Section default (company vs individual)

Pure-math, DB-free.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.core.constants import TDSDeducteeType
from app.core.tds_ldc import LDCContext, LDCNotAppliedReason, select_tds_rate

# ---------------------------------------------------------------------------
# Fixtures.
# ---------------------------------------------------------------------------

_DEFAULT_KWARGS = dict(
    rate_no_pan=Decimal("20.00"),
    rate_individual=Decimal("10.00"),
    rate_company=Decimal("10.00"),
    deductee_type=TDSDeducteeType.INDIVIDUAL,
    has_pan=True,
    deduction_date=date(2025, 5, 15),
    base_amount=Decimal("100000"),
)


def _valid_ldc(**overrides) -> LDCContext:
    """LDC that is valid on 2025-05-15, at 2% rate, ₹10L cap, nothing utilised."""
    base = dict(
        certificate_no="LDC/194J/2025-26/123",
        rate=Decimal("2.00"),
        limit=Decimal("1000000"),
        valid_from=date(2025, 4, 1),
        valid_until=date(2026, 3, 31),
        utilized=Decimal("0.00"),
    )
    base.update(overrides)
    return LDCContext(**base)


# ---------------------------------------------------------------------------
# §206AA — no PAN always wins.
# ---------------------------------------------------------------------------


def test_no_pan_forces_20_even_with_valid_ldc() -> None:
    """§206AA: no PAN → 20% no matter what the LDC says."""
    out = select_tds_rate(**{**_DEFAULT_KWARGS, "has_pan": False, "ldc": _valid_ldc()})
    assert out.rate == Decimal("20.00")
    assert out.ldc_applied is False
    assert out.ldc_reason is LDCNotAppliedReason.NO_PAN_OVERRIDES


def test_no_pan_no_ldc_returns_20() -> None:
    out = select_tds_rate(**{**_DEFAULT_KWARGS, "has_pan": False, "ldc": None})
    assert out.rate == Decimal("20.00")
    assert out.ldc_applied is False
    assert out.ldc_reason is LDCNotAppliedReason.NO_PAN_OVERRIDES


# ---------------------------------------------------------------------------
# LDC absent or malformed.
# ---------------------------------------------------------------------------


def test_no_ldc_falls_through_to_standard_individual() -> None:
    out = select_tds_rate(**{**_DEFAULT_KWARGS, "ldc": None})
    assert out.rate == Decimal("10.00")
    assert out.ldc_applied is False
    assert out.ldc_reason is LDCNotAppliedReason.NO_CERTIFICATE


def test_no_ldc_falls_through_to_standard_company() -> None:
    kw = {**_DEFAULT_KWARGS, "deductee_type": TDSDeducteeType.COMPANY}
    out = select_tds_rate(**{**kw, "ldc": None})
    assert out.rate == Decimal("10.00")


def test_ldc_without_cert_number_is_treated_as_no_cert() -> None:
    """An LDCContext with certificate_no=None means "no LDC on file"."""
    out = select_tds_rate(
        **{**_DEFAULT_KWARGS, "ldc": LDCContext(certificate_no=None, rate=Decimal("2.00"))}
    )
    assert out.rate == Decimal("10.00")
    assert out.ldc_applied is False
    assert out.ldc_reason is LDCNotAppliedReason.NO_CERTIFICATE


def test_ldc_with_cert_but_no_rate_is_treated_as_no_cert() -> None:
    """Half-configured LDC (cert number but no rate) is not applied."""
    out = select_tds_rate(
        **{**_DEFAULT_KWARGS, "ldc": LDCContext(certificate_no="LDC/X", rate=None)}
    )
    assert out.rate == Decimal("10.00")
    assert out.ldc_applied is False
    assert out.ldc_reason is LDCNotAppliedReason.NO_CERTIFICATE


# ---------------------------------------------------------------------------
# Happy path.
# ---------------------------------------------------------------------------


def test_valid_ldc_applies_lower_rate_individual() -> None:
    out = select_tds_rate(**{**_DEFAULT_KWARGS, "ldc": _valid_ldc()})
    assert out.rate == Decimal("2.00")
    assert out.ldc_applied is True
    assert out.ldc_reason is LDCNotAppliedReason.APPLIED
    assert out.ldc_certificate_no == "LDC/194J/2025-26/123"


def test_valid_ldc_applies_lower_rate_company() -> None:
    kw = {**_DEFAULT_KWARGS, "deductee_type": TDSDeducteeType.COMPANY}
    out = select_tds_rate(**{**kw, "ldc": _valid_ldc(rate=Decimal("1.00"))})
    assert out.rate == Decimal("1.00")
    assert out.ldc_applied is True


def test_valid_ldc_with_no_limit_is_uncapped() -> None:
    """limit=None means "uncapped" — huge deduction should still apply the LDC."""
    out = select_tds_rate(
        **{
            **_DEFAULT_KWARGS,
            "base_amount": Decimal("100000000"),  # ₹10Cr
            "ldc": _valid_ldc(limit=None),
        }
    )
    assert out.rate == Decimal("2.00")
    assert out.ldc_applied is True


def test_valid_ldc_with_no_window_boundaries_applies_anytime() -> None:
    """Both valid_from and valid_until None → cert has no validity window."""
    out = select_tds_rate(
        **{**_DEFAULT_KWARGS, "ldc": _valid_ldc(valid_from=None, valid_until=None)}
    )
    assert out.rate == Decimal("2.00")
    assert out.ldc_applied is True


# ---------------------------------------------------------------------------
# Validity-window boundaries.
# ---------------------------------------------------------------------------


def test_ldc_rejected_before_valid_from() -> None:
    out = select_tds_rate(
        **{
            **_DEFAULT_KWARGS,
            "deduction_date": date(2025, 3, 31),  # FY start - 1
            "ldc": _valid_ldc(),
        }
    )
    assert out.rate == Decimal("10.00")
    assert out.ldc_applied is False
    assert out.ldc_reason is LDCNotAppliedReason.NOT_YET_VALID


def test_ldc_applied_on_valid_from_boundary() -> None:
    """Boundary-inclusive: deduction on valid_from itself should apply."""
    out = select_tds_rate(
        **{**_DEFAULT_KWARGS, "deduction_date": date(2025, 4, 1), "ldc": _valid_ldc()}
    )
    assert out.rate == Decimal("2.00")
    assert out.ldc_applied is True


def test_ldc_applied_on_valid_until_boundary() -> None:
    out = select_tds_rate(
        **{**_DEFAULT_KWARGS, "deduction_date": date(2026, 3, 31), "ldc": _valid_ldc()}
    )
    assert out.rate == Decimal("2.00")
    assert out.ldc_applied is True


def test_ldc_rejected_after_valid_until() -> None:
    out = select_tds_rate(
        **{
            **_DEFAULT_KWARGS,
            "deduction_date": date(2026, 4, 1),  # FY end + 1
            "ldc": _valid_ldc(),
        }
    )
    assert out.rate == Decimal("10.00")
    assert out.ldc_applied is False
    assert out.ldc_reason is LDCNotAppliedReason.EXPIRED


# ---------------------------------------------------------------------------
# Limit checks.
# ---------------------------------------------------------------------------


def test_ldc_applied_when_limit_exactly_covers_deduction() -> None:
    """limit = utilised + base (boundary-inclusive)."""
    out = select_tds_rate(
        **{
            **_DEFAULT_KWARGS,
            "base_amount": Decimal("500000"),
            "ldc": _valid_ldc(limit=Decimal("1000000"), utilized=Decimal("500000")),
        }
    )
    assert out.rate == Decimal("2.00")
    assert out.ldc_applied is True


def test_ldc_rejected_when_limit_would_be_exceeded() -> None:
    """utilised + base > limit → fall back to standard. Protects against over-use."""
    out = select_tds_rate(
        **{
            **_DEFAULT_KWARGS,
            "base_amount": Decimal("500001"),
            "ldc": _valid_ldc(limit=Decimal("1000000"), utilized=Decimal("500000")),
        }
    )
    assert out.rate == Decimal("10.00")
    assert out.ldc_applied is False
    assert out.ldc_reason is LDCNotAppliedReason.LIMIT_EXHAUSTED


def test_ldc_rejected_when_already_fully_utilised() -> None:
    out = select_tds_rate(
        **{
            **_DEFAULT_KWARGS,
            "ldc": _valid_ldc(limit=Decimal("1000000"), utilized=Decimal("1000000")),
        }
    )
    assert out.rate == Decimal("10.00")
    assert out.ldc_applied is False
    assert out.ldc_reason is LDCNotAppliedReason.LIMIT_EXHAUSTED


# ---------------------------------------------------------------------------
# Reason is always populated (audit trail).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "reason",
    [
        LDCNotAppliedReason.APPLIED,
        LDCNotAppliedReason.NO_CERTIFICATE,
        LDCNotAppliedReason.NO_PAN_OVERRIDES,
        LDCNotAppliedReason.NOT_YET_VALID,
        LDCNotAppliedReason.EXPIRED,
        LDCNotAppliedReason.LIMIT_EXHAUSTED,
    ],
)
def test_every_ldc_reason_is_reachable(reason: LDCNotAppliedReason) -> None:
    """Every enum value is produced by at least one shape of input.

    Regression against someone silently adding an unreachable branch.
    """
    cases = {
        LDCNotAppliedReason.APPLIED: dict(ldc=_valid_ldc()),
        LDCNotAppliedReason.NO_CERTIFICATE: dict(ldc=None),
        LDCNotAppliedReason.NO_PAN_OVERRIDES: dict(has_pan=False, ldc=_valid_ldc()),
        LDCNotAppliedReason.NOT_YET_VALID: dict(deduction_date=date(2025, 3, 1), ldc=_valid_ldc()),
        LDCNotAppliedReason.EXPIRED: dict(deduction_date=date(2026, 4, 15), ldc=_valid_ldc()),
        LDCNotAppliedReason.LIMIT_EXHAUSTED: dict(ldc=_valid_ldc(utilized=Decimal("1000000"))),
    }
    out = select_tds_rate(**{**_DEFAULT_KWARGS, **cases[reason]})
    assert out.ldc_reason is reason
