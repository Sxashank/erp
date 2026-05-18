"""Lower Deduction Certificate (LDC) rate selection — pure, DB-free.

Per §197 of the Income Tax Act, a deductee may apply to the AO for a certificate
authorizing TDS at a rate lower than the section-specified rate (or nil). Until
exhausted or expired, the certificate overrides the default rate — but not the
§206AA no-PAN override, which always wins.

This module is pure-math so it can be unit-tested without a session.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from app.core.constants import TDSDeducteeType


class LDCNotAppliedReason(str, Enum):
    """Why LDC was NOT applied on a given deduction. Carried on the result for audit."""

    APPLIED = "APPLIED"  # LDC applied successfully
    NO_CERTIFICATE = "NO_CERTIFICATE"  # Vendor has no LDC on file
    NO_PAN_OVERRIDES = "NO_PAN_OVERRIDES"  # §206AA — no PAN wins over LDC
    NOT_YET_VALID = "NOT_YET_VALID"  # deduction_date < valid_from
    EXPIRED = "EXPIRED"  # deduction_date > valid_until
    LIMIT_EXHAUSTED = "LIMIT_EXHAUSTED"  # utilized + base > limit


@dataclass(frozen=True)
class LDCContext:
    """Snapshot of the vendor's LDC at the moment of a TDS computation.

    All fields optional: an `LDCContext` with `certificate_no=None` (or no rate set)
    represents "no LDC on file", and `select_tds_rate` will fall through to the
    standard rate logic.
    """

    certificate_no: str | None = None
    rate: Decimal | None = None
    limit: Decimal | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    utilized: Decimal = Decimal("0.00")


@dataclass(frozen=True)
class RateSelection:
    """Outcome of `select_tds_rate`. `ldc_applied=True` iff the chosen rate came from the LDC."""

    rate: Decimal
    ldc_applied: bool
    ldc_reason: LDCNotAppliedReason
    ldc_certificate_no: str | None


def select_tds_rate(
    *,
    rate_no_pan: Decimal,
    rate_individual: Decimal,
    rate_company: Decimal,
    deductee_type: TDSDeducteeType,
    has_pan: bool,
    deduction_date: date,
    base_amount: Decimal,
    ldc: LDCContext | None = None,
) -> RateSelection:
    """Decide which TDS rate applies for a deduction.

    Precedence (highest first):
      1. No PAN → `rate_no_pan` (§206AA). LDC does NOT override this.
      2. Valid LDC (cert present, rate set, deduction_date in window, remaining
         limit ≥ base_amount) → `ldc.rate`.
      3. Standard rate per deductee type.

    The returned `RateSelection.ldc_reason` always explains the outcome so the
    caller can persist the rationale on the TDS entry for audit.
    """
    # 1. §206AA: no PAN → 20% minimum. LDC never overrides this.
    if not has_pan:
        return RateSelection(
            rate=rate_no_pan,
            ldc_applied=False,
            ldc_reason=LDCNotAppliedReason.NO_PAN_OVERRIDES,
            ldc_certificate_no=None,
        )

    std_rate = rate_company if deductee_type == TDSDeducteeType.COMPANY else rate_individual

    # 2. No LDC on file → standard rate.
    if ldc is None or not ldc.certificate_no or ldc.rate is None:
        return RateSelection(
            rate=std_rate,
            ldc_applied=False,
            ldc_reason=LDCNotAppliedReason.NO_CERTIFICATE,
            ldc_certificate_no=None,
        )

    # 3a. Validity window.
    if ldc.valid_from is not None and deduction_date < ldc.valid_from:
        return RateSelection(
            rate=std_rate,
            ldc_applied=False,
            ldc_reason=LDCNotAppliedReason.NOT_YET_VALID,
            ldc_certificate_no=ldc.certificate_no,
        )
    if ldc.valid_until is not None and deduction_date > ldc.valid_until:
        return RateSelection(
            rate=std_rate,
            ldc_applied=False,
            ldc_reason=LDCNotAppliedReason.EXPIRED,
            ldc_certificate_no=ldc.certificate_no,
        )

    # 3b. Limit check. `limit=None` means uncapped; `limit=Decimal("0")` is a malformed cert.
    if ldc.limit is not None:
        remaining = ldc.limit - ldc.utilized
        if remaining < base_amount:
            return RateSelection(
                rate=std_rate,
                ldc_applied=False,
                ldc_reason=LDCNotAppliedReason.LIMIT_EXHAUSTED,
                ldc_certificate_no=ldc.certificate_no,
            )

    return RateSelection(
        rate=ldc.rate,
        ldc_applied=True,
        ldc_reason=LDCNotAppliedReason.APPLIED,
        ldc_certificate_no=ldc.certificate_no,
    )
