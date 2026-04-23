"""NPA classification golden tests.

Encodes the RBI IRAC bucket boundaries and provisioning rates (see
CLAUDE.md §4.8 and §7.1). Every boundary (0, 1, 30, 31, 60, 61, 90, 91,
365, 366, 730, 731, 1095, 1096, 1460, 1461) is a separate test case so a
regression on a single threshold shows up with a named failure.

These are pure-math tests — no DB involved.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock

import pytest

from app.services.lending.npa_service import (
    NPA_THRESHOLDS,
    PROVISION_RATES,
    NPAService,
)


# ---------------------------------------------------------------------------
# Threshold table — frozen constants per RBI. Changes require a migration note.
# ---------------------------------------------------------------------------

def test_npa_threshold_constants_match_rbi_spec() -> None:
    # Any edit below requires CLAUDE.md §4.8 and refdocs/Phase3_* updates.
    assert NPA_THRESHOLDS == {
        "standard": 0,
        "sma_0": 1,
        "sma_1": 31,
        "sma_2": 61,
        "substandard": 91,
        "doubtful_1": 366,
        "doubtful_2": 731,
        "doubtful_3": 1096,
        "loss": 1461,
    }


def test_provision_rates_match_rbi_spec() -> None:
    assert PROVISION_RATES["standard"] == Decimal("0.40")
    assert PROVISION_RATES["substandard_secured"] == Decimal("15.00")
    assert PROVISION_RATES["substandard_unsecured"] == Decimal("25.00")
    assert PROVISION_RATES["doubtful_1"] == Decimal("25.00")
    assert PROVISION_RATES["doubtful_2"] == Decimal("40.00")
    assert PROVISION_RATES["doubtful_3"] == Decimal("100.00")
    assert PROVISION_RATES["loss"] == Decimal("100.00")


# ---------------------------------------------------------------------------
# Classification at every boundary.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "dpd,expected",
    [
        (0, "standard"),
        (1, "sma_0"),          # first day overdue
        (15, "sma_0"),
        (30, "sma_0"),         # top of sma_0
        (31, "sma_1"),         # first day of sma_1
        (45, "sma_1"),
        (60, "sma_1"),         # top of sma_1
        (61, "sma_2"),
        (75, "sma_2"),
        (90, "sma_2"),         # top of sma_2 — still NOT yet NPA
        (91, "substandard"),   # first day of NPA
        (200, "substandard"),
        (365, "substandard"),  # top of substandard
        (366, "doubtful_1"),
        (500, "doubtful_1"),
        (730, "doubtful_1"),
        (731, "doubtful_2"),
        (900, "doubtful_2"),
        (1095, "doubtful_2"),
        (1096, "doubtful_3"),
        (1200, "doubtful_3"),
        (1460, "doubtful_3"),
        (1461, "loss"),
        (5000, "loss"),
    ],
)
@pytest.mark.asyncio
async def test_classify_loan_by_dpd(dpd: int, expected: str) -> None:
    service = NPAService(db=MagicMock())
    result = await service.classify_loan(
        loan_account_id=MagicMock(),
        dpd=dpd,
    )
    assert result == expected, f"dpd={dpd} should classify as {expected}, got {result}"


@pytest.mark.asyncio
async def test_classify_loan_rejects_negative_dpd_gracefully() -> None:
    service = NPAService(db=MagicMock())
    result = await service.classify_loan(loan_account_id=MagicMock(), dpd=-5)
    # Negative DPD is treated as standard (not overdue at all).
    assert result == "standard"


# ---------------------------------------------------------------------------
# NPA vs non-NPA discrimination.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "classification,is_npa",
    [
        ("standard", False),
        ("sma_0", False),
        ("sma_1", False),
        ("sma_2", False),          # crucial: sma_2 is NOT NPA yet
        ("substandard", True),
        ("doubtful_1", True),
        ("doubtful_2", True),
        ("doubtful_3", True),
        ("loss", True),
    ],
)
def test_is_npa(classification: str, is_npa: bool) -> None:
    service = NPAService(db=MagicMock())
    assert service.is_npa(classification) is is_npa


# ---------------------------------------------------------------------------
# Provisioning math. Secured vs unsecured branching matters for substandard.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "classification,is_secured,expected_rate",
    [
        ("standard", True, Decimal("0.40")),
        ("standard", False, Decimal("0.40")),
        ("sma_0", True, Decimal("0.40")),
        ("sma_2", True, Decimal("0.40")),
        ("substandard", True, Decimal("15.00")),
        ("substandard", False, Decimal("25.00")),
        ("doubtful_1", True, Decimal("25.00")),
        ("doubtful_1", False, Decimal("25.00")),  # no secured/unsecured split at doubtful
        ("doubtful_2", True, Decimal("40.00")),
        ("doubtful_3", True, Decimal("100.00")),
        ("loss", True, Decimal("100.00")),
    ],
)
@pytest.mark.asyncio
async def test_calculate_provision_rate(
    classification: str,
    is_secured: bool,
    expected_rate: Decimal,
) -> None:
    # Mock the loan row so we skip DB access.
    fake_loan = MagicMock()
    fake_loan.principal_outstanding = Decimal("1000000.00")
    fake_loan.interest_outstanding = Decimal("50000.00")

    db = MagicMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = fake_loan
    db.execute = AsyncMock(return_value=result_mock)

    service = NPAService(db=db)
    out = await service.calculate_provision(
        loan_account_id=MagicMock(),
        classification=classification,
        is_secured=is_secured,
    )

    assert out["provision_rate"] == expected_rate
    expected_amount = (
        (Decimal("1000000.00") + Decimal("50000.00")) * expected_rate / Decimal("100")
    )
    assert out["provision_amount"] == expected_amount
    assert out["outstanding_amount"] == Decimal("1050000.00")
    assert out["is_npa"] == service.is_npa(classification)


@pytest.mark.asyncio
async def test_calculate_provision_rejects_missing_loan() -> None:
    db = MagicMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result_mock)

    service = NPAService(db=db)
    with pytest.raises(ValueError, match="not found"):
        await service.calculate_provision(
            loan_account_id=MagicMock(),
            classification="substandard",
            is_secured=True,
        )
