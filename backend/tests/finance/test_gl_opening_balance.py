"""Opening-balance cutoff priority tests (STAGE-4-PENDING-009 closure).

`GLPostingService.get_trial_balance` must compute opening balance as of:
  1. If `period_id` given → the period's start_date.
  2. Else if `financial_year_id` given → the FY's start_date.
  3. Else → April 1 of the current fiscal year (derived from `as_of_date`
     or today()), matching India's April–March fiscal calendar
     (CLAUDE.md §7.1).

These tests pin the priority chain by stubbing `session.get()` for
`FinancialPeriod` / `FinancialYear` lookups and capturing the cutoff
passed to `gl_repo.get_account_balance_before_date`.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.finance.financial_year import FinancialPeriod, FinancialYear
from app.services.finance.gl_posting_service import GLPostingService


ACC_ID = uuid4()
ORG_ID = uuid4()


def _row() -> dict:
    return {
        "account_id": ACC_ID,
        "account_code": "1000",
        "account_name": "Cash",
        "account_group_id": uuid4(),
        "account_group_name": "Assets",
        "total_debit": Decimal("500.00"),
        "total_credit": Decimal("200.00"),
    }


@pytest.fixture
def service() -> GLPostingService:
    svc = GLPostingService(session=MagicMock())
    svc.gl_repo = MagicMock()
    svc.gl_repo.get_trial_balance_data = AsyncMock(return_value=[_row()])
    svc.gl_repo.get_account_balance_before_date = AsyncMock(
        return_value=(Decimal("100.00"), Decimal("30.00"))
    )
    return svc


async def _lookup_capture() -> tuple[dict, AsyncMock]:
    """Return a side-effect mock that records all `session.get(Model, id)` calls."""
    seen: dict = {"calls": []}

    async def _get(model, pk):
        seen["calls"].append((model, pk))
        return seen.get(model)

    return seen, AsyncMock(side_effect=_get)


@pytest.mark.asyncio
async def test_cutoff_uses_period_start_when_period_id_given(
    service: GLPostingService,
) -> None:
    """Priority 1: `period_id` present → use period.start_date."""
    period_id = uuid4()
    fy_id = uuid4()
    period = SimpleNamespace(start_date=date(2026, 7, 1), name="Q2")
    fy = SimpleNamespace(start_date=date(2026, 4, 1), name="FY2026-27")

    seen, mock_get = await _lookup_capture()
    seen[FinancialPeriod] = period
    seen[FinancialYear] = fy
    service.session.get = mock_get

    await service.get_trial_balance(
        organization_id=ORG_ID,
        financial_year_id=fy_id,
        period_id=period_id,
    )

    # Priority 1 hit: opening cutoff is period.start_date (2026-07-01).
    service.gl_repo.get_account_balance_before_date.assert_awaited_once_with(
        ACC_ID, date(2026, 7, 1)
    )


@pytest.mark.asyncio
async def test_cutoff_falls_back_to_fy_start_when_no_period(
    service: GLPostingService,
) -> None:
    """Priority 2: `period_id` None but `financial_year_id` present → FY.start_date."""
    fy_id = uuid4()
    fy = SimpleNamespace(start_date=date(2026, 4, 1), name="FY2026-27")

    seen, mock_get = await _lookup_capture()
    seen[FinancialYear] = fy
    service.session.get = mock_get

    await service.get_trial_balance(
        organization_id=ORG_ID,
        financial_year_id=fy_id,
        period_id=None,
    )
    service.gl_repo.get_account_balance_before_date.assert_awaited_once_with(
        ACC_ID, date(2026, 4, 1)
    )


@pytest.mark.asyncio
async def test_cutoff_falls_back_to_april_1_same_year_when_as_of_after_april(
    service: GLPostingService,
) -> None:
    """Priority 3a: neither period nor FY resolves, as_of_date >= April → April 1
    of the same calendar year."""
    # FY lookup returns None so we hit the ultimate fallback.
    service.session.get = AsyncMock(return_value=None)

    await service.get_trial_balance(
        organization_id=ORG_ID,
        financial_year_id=uuid4(),
        period_id=None,
        as_of_date=date(2026, 10, 15),
    )
    service.gl_repo.get_account_balance_before_date.assert_awaited_once_with(
        ACC_ID, date(2026, 4, 1)
    )


@pytest.mark.asyncio
async def test_cutoff_falls_back_to_april_1_previous_year_when_as_of_before_april(
    service: GLPostingService,
) -> None:
    """Priority 3b: as_of_date < April → April 1 of the PREVIOUS calendar year
    (we are still in the prior fiscal year)."""
    service.session.get = AsyncMock(return_value=None)

    await service.get_trial_balance(
        organization_id=ORG_ID,
        financial_year_id=uuid4(),
        period_id=None,
        as_of_date=date(2027, 2, 15),  # Feb 2027 — still FY2026-27
    )
    service.gl_repo.get_account_balance_before_date.assert_awaited_once_with(
        ACC_ID, date(2026, 4, 1)
    )


@pytest.mark.asyncio
async def test_opening_balance_flows_through_to_trial_balance_rows(
    service: GLPostingService,
) -> None:
    """Opening debit 100 / credit 30 → opening_balance 70 → slots into opening_debit."""
    fy_id = uuid4()
    fy = SimpleNamespace(start_date=date(2026, 4, 1), name="FY")

    seen, mock_get = await _lookup_capture()
    seen[FinancialYear] = fy
    service.session.get = mock_get

    response = await service.get_trial_balance(
        organization_id=ORG_ID,
        financial_year_id=fy_id,
        period_id=None,
    )
    assert len(response.items) == 1
    item = response.items[0]
    assert item.opening_debit == Decimal("70.00")
    assert item.opening_credit == Decimal("0.00")
    # Period activity: debit 500 - credit 200 = 300. Closing = 70 + 300 = 370 debit.
    assert item.closing_debit == Decimal("370.00")
    assert item.closing_credit == Decimal("0.00")
