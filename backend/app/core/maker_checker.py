"""Maker-checker invariant helper (STAGE-4-PENDING-004 closure).

CLAUDE.md §8.4 / §7.1:
  - High-risk actions (sanction, disbursement authorize, voucher post >
    amount band, payroll finalize, OTS, rate reset, rate change, write-off,
    KYC approve, role grant, large refund/reversal, bank-account change,
    salary-structure change) require a two-person workflow.
  - The MAKER cannot also be the CHECKER — enforced here.
  - Delegated-authority routing: the required approval level depends on
    the amount band (officer → GM → ED → CMD → Board for lending).

This module provides a single helper used by every approval endpoint +
pure amount-band routing used by the workflow engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Iterable
from uuid import UUID

from app.core.exceptions import AppException, ForbiddenException


class MakerCheckerViolationError(ForbiddenException):
    """Raised when the maker and checker are the same user."""

    def __init__(self, detail: str = "Maker cannot approve their own submission") -> None:
        super().__init__(detail=detail)
        self.error_code = "MAKER_EQUALS_CHECKER"


class ApprovalLevel(str, Enum):
    """Approval authority ranks. Higher rank = more authority.

    Values are stringly-typed for DB persistence; the ordering is encoded
    in `_RANK` below.
    """
    OFFICER = "officer"
    MANAGER = "manager"
    GM = "gm"
    ED = "ed"
    CMD = "cmd"
    BOARD = "board"


_RANK: dict[ApprovalLevel, int] = {
    ApprovalLevel.OFFICER: 1,
    ApprovalLevel.MANAGER: 2,
    ApprovalLevel.GM: 3,
    ApprovalLevel.ED: 4,
    ApprovalLevel.CMD: 5,
    ApprovalLevel.BOARD: 6,
}


def ensure_maker_is_not_checker(
    *,
    maker_user_id: UUID | str | None,
    checker_user_id: UUID | str | None,
) -> None:
    """Raise if the maker and the checker are the same user.

    Accepts either UUID or string for flexibility; normalises before the
    comparison so an ORM UUID column doesn't accidentally compare unequal
    to a str from JWT `sub`."""
    if maker_user_id is None or checker_user_id is None:
        # Don't silently allow — absence of a maker is a programming bug.
        raise MakerCheckerViolationError(
            detail="Maker and checker identities must both be supplied"
        )
    if str(maker_user_id) == str(checker_user_id):
        raise MakerCheckerViolationError()


# ---------------------------------------------------------------------------
# Delegated-authority routing for lending sanctions.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AuthorityBand:
    """One row of the delegation matrix: if amount ≤ ceiling, required_level
    is enough to approve."""
    ceiling: Decimal
    required_level: ApprovalLevel


# Bands per the refdocs (Phase 3 §Sanction): up to 10 Cr → Officer; 10-50 Cr
# → GM; 50-100 Cr → ED; 100-500 Cr → CMD; > 500 Cr → Board.
DEFAULT_LENDING_BANDS: tuple[AuthorityBand, ...] = (
    AuthorityBand(ceiling=Decimal("100000000"), required_level=ApprovalLevel.OFFICER),    # ≤ 10 Cr
    AuthorityBand(ceiling=Decimal("500000000"), required_level=ApprovalLevel.GM),         # ≤ 50 Cr
    AuthorityBand(ceiling=Decimal("1000000000"), required_level=ApprovalLevel.ED),        # ≤ 100 Cr
    AuthorityBand(ceiling=Decimal("5000000000"), required_level=ApprovalLevel.CMD),       # ≤ 500 Cr
    AuthorityBand(ceiling=Decimal("Infinity"), required_level=ApprovalLevel.BOARD),       # > 500 Cr
)


def required_level_for_amount(
    amount: Decimal,
    bands: Iterable[AuthorityBand] = DEFAULT_LENDING_BANDS,
) -> ApprovalLevel:
    """Return the minimum ApprovalLevel that can authorise `amount`."""
    if amount < 0:
        raise ValueError("amount must be non-negative")
    for band in bands:
        if amount <= band.ceiling:
            return band.required_level
    # Never reached because the last band has ceiling=Infinity.
    return ApprovalLevel.BOARD  # pragma: no cover


def can_approve(
    approver_level: ApprovalLevel,
    amount: Decimal,
    bands: Iterable[AuthorityBand] = DEFAULT_LENDING_BANDS,
) -> bool:
    """True iff `approver_level` meets or exceeds the required level for `amount`."""
    required = required_level_for_amount(amount, bands)
    return _RANK[approver_level] >= _RANK[required]


# ---------------------------------------------------------------------------
# Workflow-init helper used by lending/application, lending/sanction,
# lending/rating services (STAGE-4-PENDING-010 closure).
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WorkflowInitRequest:
    """Values the workflow engine needs to route an approval.

    The engine consumes this struct; services build it from their domain
    object (loan application, sanction, rating). Keeps the workflow engine
    from depending on every domain service.
    """
    workflow_code: str        # e.g. "LOAN_SANCTION_APPROVAL"
    entity_type: str          # e.g. "loan_sanction"
    entity_id: UUID
    maker_user_id: UUID
    organization_id: UUID
    amount: Decimal | None = None
    required_level: ApprovalLevel | None = None
    priority: str = "normal"  # normal | high | urgent


def build_workflow_request(
    *,
    workflow_code: str,
    entity_type: str,
    entity_id: UUID,
    maker_user_id: UUID,
    organization_id: UUID,
    amount: Decimal | None = None,
    bands: Iterable[AuthorityBand] = DEFAULT_LENDING_BANDS,
    priority: str = "normal",
) -> WorkflowInitRequest:
    """Construct a WorkflowInitRequest, inferring required_level from amount."""
    required = required_level_for_amount(amount, bands) if amount is not None else None
    return WorkflowInitRequest(
        workflow_code=workflow_code,
        entity_type=entity_type,
        entity_id=entity_id,
        maker_user_id=maker_user_id,
        organization_id=organization_id,
        amount=amount,
        required_level=required,
        priority=priority,
    )
