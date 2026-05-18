"""GL posting balance invariant tests.

CLAUDE.md §4.3 / §7.1: every voucher must balance — Σ debit = Σ credit.
The enforcement site is `gl_posting_service.post_from_source` around line 186.
These tests assert the invariant fires for every mis-balanced case.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import BadRequestException
from app.services.finance.gl_posting_service import GLPostingService


def _kwargs(lines):  # helper: common required kwargs for post_from_source
    from datetime import date

    return dict(
        source_type=MagicMock(),
        source_id=uuid4(),
        source_reference="V1",
        organization_id=uuid4(),
        financial_year_id=uuid4(),
        period_id=uuid4(),
        voucher_date=date(2026, 4, 23),
        narration="",
        lines=lines,
        posted_by=uuid4(),
    )


@pytest.fixture
def service() -> GLPostingService:
    svc = GLPostingService(session=MagicMock())
    svc.gl_repo = MagicMock()
    svc.account_repo = MagicMock()
    # Default: period is open. Individual tests can override via
    # `_bind_period(service, _period(is_closed=True))` to test the guard.
    from types import SimpleNamespace

    default_period = SimpleNamespace(is_closed=False, is_locked=False, name="TEST_PERIOD")
    svc.session.get = AsyncMock(return_value=default_period)
    return svc


@pytest.mark.asyncio
async def test_empty_lines_rejected(service: GLPostingService) -> None:
    with pytest.raises(BadRequestException, match="No lines"):
        await service.post_from_source(**_kwargs(lines=[]))


@pytest.mark.asyncio
async def test_debit_credit_mismatch_rejected(service: GLPostingService) -> None:
    lines = [
        {"account_id": uuid4(), "debit_amount": Decimal("100.00"), "credit_amount": Decimal("0")},
        {"account_id": uuid4(), "debit_amount": Decimal("0"), "credit_amount": Decimal("50.00")},
    ]
    with pytest.raises(BadRequestException, match="not balanced"):
        await service.post_from_source(**_kwargs(lines=lines))


@pytest.mark.asyncio
async def test_fractional_mismatch_rejected(service: GLPostingService) -> None:
    # 100.00 vs 99.99 — the check is exact equality, no tolerance.
    lines = [
        {"account_id": uuid4(), "debit_amount": Decimal("100.00"), "credit_amount": Decimal("0")},
        {"account_id": uuid4(), "debit_amount": Decimal("0"), "credit_amount": Decimal("99.99")},
    ]
    with pytest.raises(BadRequestException, match="not balanced"):
        await service.post_from_source(**_kwargs(lines=lines))


@pytest.mark.asyncio
async def test_balanced_posting_proceeds_past_the_balance_check(service: GLPostingService) -> None:
    """A balanced posting should fail LATER (at account lookup), NOT at
    the balance check. Proves the invariant is symmetric."""
    lines = [
        {"account_id": uuid4(), "debit_amount": Decimal("100.00"), "credit_amount": Decimal("0")},
        {"account_id": uuid4(), "debit_amount": Decimal("0"), "credit_amount": Decimal("100.00")},
    ]
    service.account_repo.get = AsyncMock(return_value=None)

    from app.core.exceptions import NotFoundException

    with pytest.raises(NotFoundException, match="Account not found"):
        await service.post_from_source(**_kwargs(lines=lines))


@pytest.mark.asyncio
async def test_balance_across_many_lines(service: GLPostingService) -> None:
    """5 debit lines + 3 credit lines summing to the same total should pass
    the balance check."""
    debits = [Decimal("25"), Decimal("25"), Decimal("25"), Decimal("15"), Decimal("10")]
    credits = [Decimal("30"), Decimal("40"), Decimal("30")]
    lines = (
        [{"account_id": uuid4(), "debit_amount": d, "credit_amount": Decimal("0")} for d in debits]
        + [
            {"account_id": uuid4(), "debit_amount": Decimal("0"), "credit_amount": c}
            for c in credits
        ]
    )
    service.account_repo.get = AsyncMock(return_value=None)

    from app.core.exceptions import NotFoundException

    with pytest.raises(NotFoundException):
        await service.post_from_source(**_kwargs(lines=lines))


@pytest.mark.asyncio
async def test_both_zero_lines_rejected(service: GLPostingService) -> None:
    """Lines that sum to zero debit AND zero credit are technically
    'balanced' but meaningless. The GL service must reject them before any
    account lookup or voucher creation."""
    lines = [
        {"account_id": uuid4(), "debit_amount": Decimal("0"), "credit_amount": Decimal("0")},
    ]
    service.account_repo.get = AsyncMock(return_value=None)

    with pytest.raises(BadRequestException, match="Zero-value"):
        await service.post_from_source(**_kwargs(lines=lines))


# ---------------------------------------------------------------------------
# HARD_CLOSED / SOFT_LOCKED period guard (STAGE-4-PENDING-003 closure).
# See CLAUDE.md §4.3 / §7.1.
# ---------------------------------------------------------------------------

def _period(*, is_closed: bool = False, is_locked: bool = False, name: str = "Apr 2026"):
    """Minimal test-only period row — only the attributes the guard reads."""
    from types import SimpleNamespace

    return SimpleNamespace(is_closed=is_closed, is_locked=is_locked, name=name)


@pytest.mark.asyncio
async def test_hard_closed_period_rejects_posting(service: GLPostingService) -> None:
    """Posting to a HARD_CLOSED period fails fast with ClosedPeriodError."""
    from app.core.exceptions import ClosedPeriodError

    service.session.get = AsyncMock(return_value=_period(is_closed=True, name="Apr 2026"))
    lines = [
        {"account_id": uuid4(), "debit_amount": Decimal("100"), "credit_amount": Decimal("0")},
        {"account_id": uuid4(), "debit_amount": Decimal("0"), "credit_amount": Decimal("100")},
    ]

    with pytest.raises(ClosedPeriodError) as exc:
        await service.post_from_source(**_kwargs(lines=lines))
    assert exc.value.error_code == "CLOSED_PERIOD"
    assert "Apr 2026" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_locked_period_rejects_posting(service: GLPostingService) -> None:
    """Posting to a SOFT_LOCKED period also raises ClosedPeriodError."""
    from app.core.exceptions import ClosedPeriodError

    service.session.get = AsyncMock(return_value=_period(is_locked=True, name="Mar 2026"))
    lines = [
        {"account_id": uuid4(), "debit_amount": Decimal("100"), "credit_amount": Decimal("0")},
        {"account_id": uuid4(), "debit_amount": Decimal("0"), "credit_amount": Decimal("100")},
    ]

    with pytest.raises(ClosedPeriodError) as exc:
        await service.post_from_source(**_kwargs(lines=lines))
    assert "locked" in str(exc.value.detail).lower()


@pytest.mark.asyncio
async def test_missing_period_rejected(service: GLPostingService) -> None:
    """session.get returning None means the period_id is bogus — 404."""
    from app.core.exceptions import NotFoundException

    service.session.get = AsyncMock(return_value=None)
    lines = [
        {"account_id": uuid4(), "debit_amount": Decimal("100"), "credit_amount": Decimal("0")},
        {"account_id": uuid4(), "debit_amount": Decimal("0"), "credit_amount": Decimal("100")},
    ]
    with pytest.raises(NotFoundException, match="Financial period"):
        await service.post_from_source(**_kwargs(lines=lines))


@pytest.mark.asyncio
async def test_open_period_proceeds_past_the_guard(service: GLPostingService) -> None:
    """An open period reaches the balance check and then the account lookup.
    Proves the guard is symmetric — it only blocks closed/locked."""
    from app.core.exceptions import NotFoundException

    # service fixture already binds an open period by default.
    service.account_repo.get = AsyncMock(return_value=None)

    lines = [
        {"account_id": uuid4(), "debit_amount": Decimal("100"), "credit_amount": Decimal("0")},
        {"account_id": uuid4(), "debit_amount": Decimal("0"), "credit_amount": Decimal("100")},
    ]
    with pytest.raises(NotFoundException, match="Account not found"):
        await service.post_from_source(**_kwargs(lines=lines))
