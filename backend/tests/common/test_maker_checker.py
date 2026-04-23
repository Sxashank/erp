"""Maker-checker + authority-band tests (STAGE-4-PENDING-004 + -010 closure)."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.maker_checker import (
    DEFAULT_LENDING_BANDS,
    ApprovalLevel,
    AuthorityBand,
    MakerCheckerViolationError,
    build_workflow_request,
    can_approve,
    ensure_maker_is_not_checker,
    required_level_for_amount,
)


# ---------------------------------------------------------------------------
# ensure_maker_is_not_checker.
# ---------------------------------------------------------------------------

def test_passes_when_users_differ() -> None:
    ensure_maker_is_not_checker(
        maker_user_id=uuid4(),
        checker_user_id=uuid4(),
    )


def test_rejects_when_users_identical() -> None:
    u = uuid4()
    with pytest.raises(MakerCheckerViolationError) as exc:
        ensure_maker_is_not_checker(maker_user_id=u, checker_user_id=u)
    assert exc.value.error_code == "MAKER_EQUALS_CHECKER"


def test_rejects_when_either_id_is_none() -> None:
    with pytest.raises(MakerCheckerViolationError):
        ensure_maker_is_not_checker(maker_user_id=None, checker_user_id=uuid4())
    with pytest.raises(MakerCheckerViolationError):
        ensure_maker_is_not_checker(maker_user_id=uuid4(), checker_user_id=None)


def test_normalises_uuid_vs_string() -> None:
    """UUID column from ORM vs str from JWT sub — same user, must block."""
    u = uuid4()
    with pytest.raises(MakerCheckerViolationError):
        ensure_maker_is_not_checker(maker_user_id=u, checker_user_id=str(u))


# ---------------------------------------------------------------------------
# Authority bands.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "amount,expected",
    [
        (Decimal("0"), ApprovalLevel.OFFICER),
        (Decimal("50000000"), ApprovalLevel.OFFICER),         # ₹5 Cr
        (Decimal("100000000"), ApprovalLevel.OFFICER),        # exactly ₹10 Cr
        (Decimal("100000001"), ApprovalLevel.GM),             # just above ₹10 Cr
        (Decimal("250000000"), ApprovalLevel.GM),             # ₹25 Cr
        (Decimal("500000000"), ApprovalLevel.GM),             # ₹50 Cr
        (Decimal("500000001"), ApprovalLevel.ED),             # just above ₹50 Cr
        (Decimal("1000000000"), ApprovalLevel.ED),            # ₹100 Cr
        (Decimal("1000000001"), ApprovalLevel.CMD),
        (Decimal("5000000000"), ApprovalLevel.CMD),           # ₹500 Cr
        (Decimal("5000000001"), ApprovalLevel.BOARD),
        (Decimal("100000000000"), ApprovalLevel.BOARD),       # > ₹10,000 Cr
    ],
)
def test_required_level_spans_every_band(amount: Decimal, expected: ApprovalLevel) -> None:
    assert required_level_for_amount(amount) == expected


def test_required_level_rejects_negative_amount() -> None:
    with pytest.raises(ValueError):
        required_level_for_amount(Decimal("-1"))


# ---------------------------------------------------------------------------
# can_approve.
# ---------------------------------------------------------------------------

def test_officer_can_approve_small_loans() -> None:
    assert can_approve(ApprovalLevel.OFFICER, Decimal("1000000")) is True


def test_officer_cannot_approve_large_loans() -> None:
    assert can_approve(ApprovalLevel.OFFICER, Decimal("500000000")) is False


def test_board_can_approve_anything() -> None:
    assert can_approve(ApprovalLevel.BOARD, Decimal("100000000000")) is True


def test_ed_can_approve_up_to_100cr_but_not_over() -> None:
    assert can_approve(ApprovalLevel.ED, Decimal("1000000000")) is True
    assert can_approve(ApprovalLevel.ED, Decimal("1500000000")) is False


def test_higher_rank_can_always_approve_below_their_band() -> None:
    """If GM can approve ₹30 Cr, ED must also be able to."""
    amount = Decimal("300000000")
    assert can_approve(ApprovalLevel.GM, amount) is True
    assert can_approve(ApprovalLevel.ED, amount) is True
    assert can_approve(ApprovalLevel.CMD, amount) is True
    assert can_approve(ApprovalLevel.BOARD, amount) is True


# ---------------------------------------------------------------------------
# Custom band table (e.g. for a different product).
# ---------------------------------------------------------------------------

def test_custom_bands_override_defaults() -> None:
    tight_bands = (
        AuthorityBand(ceiling=Decimal("100000"), required_level=ApprovalLevel.OFFICER),
        AuthorityBand(ceiling=Decimal("1000000"), required_level=ApprovalLevel.MANAGER),
        AuthorityBand(ceiling=Decimal("Infinity"), required_level=ApprovalLevel.GM),
    )
    assert required_level_for_amount(Decimal("50000"), tight_bands) == ApprovalLevel.OFFICER
    assert required_level_for_amount(Decimal("500000"), tight_bands) == ApprovalLevel.MANAGER
    assert required_level_for_amount(Decimal("5000000"), tight_bands) == ApprovalLevel.GM


def test_default_bands_cover_infinity() -> None:
    assert DEFAULT_LENDING_BANDS[-1].ceiling == Decimal("Infinity")


# ---------------------------------------------------------------------------
# build_workflow_request.
# ---------------------------------------------------------------------------

def test_build_workflow_request_infers_required_level_from_amount() -> None:
    maker = uuid4()
    org = uuid4()
    eid = uuid4()
    req = build_workflow_request(
        workflow_code="LOAN_SANCTION_APPROVAL",
        entity_type="loan_sanction",
        entity_id=eid,
        maker_user_id=maker,
        organization_id=org,
        amount=Decimal("250000000"),  # ₹25 Cr
    )
    assert req.workflow_code == "LOAN_SANCTION_APPROVAL"
    assert req.entity_id == eid
    assert req.maker_user_id == maker
    assert req.amount == Decimal("250000000")
    assert req.required_level == ApprovalLevel.GM
    assert req.priority == "normal"


def test_build_workflow_request_without_amount() -> None:
    """Some approvals (KYC, role grant) don't have an amount — required_level stays None."""
    req = build_workflow_request(
        workflow_code="KYC_APPROVAL",
        entity_type="kyc_record",
        entity_id=uuid4(),
        maker_user_id=uuid4(),
        organization_id=uuid4(),
    )
    assert req.amount is None
    assert req.required_level is None


def test_build_workflow_request_preserves_priority() -> None:
    req = build_workflow_request(
        workflow_code="LOAN_SANCTION_APPROVAL",
        entity_type="loan_sanction",
        entity_id=uuid4(),
        maker_user_id=uuid4(),
        organization_id=uuid4(),
        amount=Decimal("100000"),
        priority="urgent",
    )
    assert req.priority == "urgent"
