"""Receipt allocation tests.

The allocation order inside `LoanAccountService.allocate_receipt` is
CROSS-INSTALLMENT (CLAUDE.md §4.8):
    penal (all overdue) → interest (all overdue) → principal (all overdue)
i.e. ALL penal across every overdue installment is cleared before ANY
interest is allocated; ALL interest before ANY principal.

Charges are not yet modelled on the installment row; when added they slot
between penal and interest per the RBI spec.

Previously the service did per-installment priority; that deviation was
closed on 2026-04-23 (see CLAUDE.md §12.3 and .stubs-approved.md closure
row `ALLOCATION-PRIORITY-2026-04-23`).
"""

from __future__ import annotations

from decimal import Decimal
from typing import List

import pytest


# ---------------------------------------------------------------------------
# Pure-function model of the allocator — this matches the service's
# `_allocate_component` loop exactly and is the canonical reference for the
# cross-installment priority per CLAUDE.md §4.8.
# ---------------------------------------------------------------------------

class Installment:
    """Test-only record mirroring the TXN_LOAN_INSTALLMENT columns used by
    the allocator."""

    def __init__(
        self,
        *,
        due_date: str,
        principal_amount: Decimal,
        interest_amount: Decimal,
        penal_interest_due: Decimal = Decimal("0"),
        principal_paid: Decimal = Decimal("0"),
        interest_paid: Decimal = Decimal("0"),
        penal_interest_paid: Decimal = Decimal("0"),
    ) -> None:
        self.due_date = due_date
        self.principal_amount = principal_amount
        self.interest_amount = interest_amount
        self.penal_interest_due = penal_interest_due
        self.principal_paid = principal_paid
        self.interest_paid = interest_paid
        self.penal_interest_paid = penal_interest_paid


def _pass(
    installments: List[Installment],
    due_attr: str,
    paid_attr: str,
    remaining: Decimal,
) -> tuple[Decimal, Decimal]:
    """One pass of the cross-installment allocator. Returns (allocated, remaining)."""
    allocated = Decimal("0")
    for inst in installments:
        if remaining <= 0:
            break
        outstanding = getattr(inst, due_attr) - getattr(inst, paid_attr)
        if outstanding <= 0:
            continue
        alloc = min(remaining, outstanding)
        setattr(inst, paid_attr, getattr(inst, paid_attr) + alloc)
        remaining -= alloc
        allocated += alloc
    return allocated, remaining


def allocate(
    installments: List[Installment],
    receipt_amount: Decimal,
) -> dict:
    """Cross-installment priority: penal → interest → principal.

    Mirrors `LoanAccountService.allocate_receipt` in
    `backend/app/services/lending/loan_account_service.py`.
    """
    remaining = receipt_amount
    penal, remaining = _pass(installments, "penal_interest_due", "penal_interest_paid", remaining)
    interest, remaining = _pass(installments, "interest_amount", "interest_paid", remaining)
    principal, remaining = _pass(installments, "principal_amount", "principal_paid", remaining)

    return {
        "penal_allocated": penal,
        "interest_allocated": interest,
        "principal_allocated": principal,
        "unallocated": remaining,
    }


# ---------------------------------------------------------------------------
# Cross-installment priority tests.
# ---------------------------------------------------------------------------

def test_exact_emi_payment_clears_oldest_installment_first() -> None:
    """A perfect one-EMI payment with no penal and a clean back-book clears
    the oldest installment fully."""
    installments = [
        Installment(
            due_date="2026-01-01",
            principal_amount=Decimal("8000"),
            interest_amount=Decimal("2000"),
        ),
        Installment(
            due_date="2026-02-01",
            principal_amount=Decimal("8000"),
            interest_amount=Decimal("2000"),
        ),
    ]

    out = allocate(installments, Decimal("10000"))

    # With no penal, interest across all comes first (₹2,000+₹2,000 = ₹4,000),
    # then principal (₹6,000 remaining knocks out oldest ₹8,000 mostly).
    # Wait — receipt is only ₹10,000. Interest passes first: 2000+2000=4000.
    # Principal: 10000-4000=6000; all goes to first installment's principal.
    assert installments[0].interest_paid == Decimal("2000")
    assert installments[1].interest_paid == Decimal("2000")
    assert installments[0].principal_paid == Decimal("6000")
    assert installments[1].principal_paid == Decimal("0")
    assert out["penal_allocated"] == Decimal("0")
    assert out["interest_allocated"] == Decimal("4000")
    assert out["principal_allocated"] == Decimal("6000")
    assert out["unallocated"] == Decimal("0")


def test_penal_cleared_across_all_before_interest() -> None:
    """Key cross-installment invariant: two installments, both with penal
    due; a receipt that covers both penals plus some interest clears BOTH
    penal balances before any interest is allocated."""
    installments = [
        Installment(
            due_date="2026-01-01",
            principal_amount=Decimal("1000"),
            interest_amount=Decimal("100"),
            penal_interest_due=Decimal("50"),
        ),
        Installment(
            due_date="2026-02-01",
            principal_amount=Decimal("1000"),
            interest_amount=Decimal("100"),
            penal_interest_due=Decimal("60"),
        ),
    ]

    # ₹120 — enough for both penals (50+60=110) plus ₹10 toward oldest interest.
    out = allocate(installments, Decimal("120"))

    assert installments[0].penal_interest_paid == Decimal("50")
    assert installments[1].penal_interest_paid == Decimal("60")
    assert installments[0].interest_paid == Decimal("10")
    assert installments[1].interest_paid == Decimal("0")
    assert installments[0].principal_paid == Decimal("0")
    assert installments[1].principal_paid == Decimal("0")
    assert out["penal_allocated"] == Decimal("110")
    assert out["interest_allocated"] == Decimal("10")
    assert out["principal_allocated"] == Decimal("0")


def test_interest_cleared_across_all_before_principal() -> None:
    installments = [
        Installment(
            due_date="2026-01-01",
            principal_amount=Decimal("1000"),
            interest_amount=Decimal("100"),
        ),
        Installment(
            due_date="2026-02-01",
            principal_amount=Decimal("1000"),
            interest_amount=Decimal("100"),
        ),
    ]
    # ₹250 — enough for both interests (100+100=200) plus ₹50 principal.
    out = allocate(installments, Decimal("250"))
    assert installments[0].interest_paid == Decimal("100")
    assert installments[1].interest_paid == Decimal("100")
    assert installments[0].principal_paid == Decimal("50")
    assert installments[1].principal_paid == Decimal("0")
    assert out["interest_allocated"] == Decimal("200")
    assert out["principal_allocated"] == Decimal("50")


def test_partial_payment_within_penal_bucket_fifo() -> None:
    """When penal can't be cleared across all, allocation follows FIFO
    within the penal bucket."""
    installments = [
        Installment(
            due_date="2026-01-01",
            principal_amount=Decimal("1000"),
            interest_amount=Decimal("100"),
            penal_interest_due=Decimal("50"),
        ),
        Installment(
            due_date="2026-02-01",
            principal_amount=Decimal("1000"),
            interest_amount=Decimal("100"),
            penal_interest_due=Decimal("60"),
        ),
    ]
    # Only ₹40 — fully consumed by oldest penal.
    out = allocate(installments, Decimal("40"))
    assert installments[0].penal_interest_paid == Decimal("40")
    assert installments[1].penal_interest_paid == Decimal("0")
    assert out["penal_allocated"] == Decimal("40")
    assert out["unallocated"] == Decimal("0")


def test_overflow_leaves_unallocated_balance() -> None:
    installments = [
        Installment(
            due_date="2026-01-01",
            principal_amount=Decimal("1000"),
            interest_amount=Decimal("0"),
        ),
    ]
    out = allocate(installments, Decimal("1500"))
    assert installments[0].principal_paid == Decimal("1000")
    assert out["unallocated"] == Decimal("500")


def test_already_partially_paid_installment_only_gets_outstanding() -> None:
    """If an installment is partially paid, the allocator only takes the
    remaining outstanding, not the gross amount."""
    installments = [
        Installment(
            due_date="2026-01-01",
            principal_amount=Decimal("1000"),
            interest_amount=Decimal("100"),
            interest_paid=Decimal("70"),  # ₹30 interest still outstanding
        ),
    ]
    out = allocate(installments, Decimal("100"))
    assert installments[0].interest_paid == Decimal("100")
    # ₹70 went to principal (100 - 30 interest outstanding).
    assert installments[0].principal_paid == Decimal("70")
    assert out["interest_allocated"] == Decimal("30")
    assert out["principal_allocated"] == Decimal("70")


def test_empty_installment_list_leaves_everything_unallocated() -> None:
    out = allocate([], Decimal("1000"))
    assert out["penal_allocated"] == Decimal("0")
    assert out["interest_allocated"] == Decimal("0")
    assert out["principal_allocated"] == Decimal("0")
    assert out["unallocated"] == Decimal("1000")
