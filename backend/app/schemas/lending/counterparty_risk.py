"""Counterparty Risk response schemas (camelCase wire format).

All money fields are ``Decimal`` (CLAUDE.md §6.2 — never floats). Pydantic
serialises Decimal to a JSON string, which the FE coerces with ``Number(...)``
for display arithmetic.

Endpoints returning these schemas must pass ``response_model_by_alias=True``
to the route decorator so FastAPI emits the camelCase aliases.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from app.schemas.base import CamelSchema

CounterpartyType = Literal["ENTITY", "LENDER", "ISSUER"]
LimitStatus = Literal["WITHIN_LIMIT", "NEAR_LIMIT", "BREACHED"]
BreachSeverity = Literal["WARNING", "BREACH", "CRITICAL"]


class CounterpartyExposureItem(CamelSchema):
    """A single counterparty row in the exposures table."""

    counterparty_id: str
    counterparty_name: str
    counterparty_type: CounterpartyType

    loan_exposure: Decimal
    investment_exposure: Decimal
    borrowing_exposure: Decimal
    total_exposure: Decimal

    tier1_capital: Decimal
    limit_amount: Decimal
    utilization_percent: Decimal
    status: LimitStatus

    rating: str | None = None
    sector: str | None = None
    is_infrastructure: bool = False


class CounterpartyExposureResponse(CamelSchema):
    """Top-N exposures plus summary cards data."""

    items: list[CounterpartyExposureItem]
    total_counterparties: int
    total_exposure: Decimal
    near_limit_count: int
    breached_count: int
    tier1_capital: Decimal
    single_borrower_limit_percent: Decimal
    infra_limit_percent: Decimal


class SectorConcentrationItem(CamelSchema):
    """Exposure aggregated by industry sector."""

    sector: str
    exposure: Decimal
    count: int
    percent_of_portfolio: Decimal


class SectorConcentrationResponse(CamelSchema):
    items: list[SectorConcentrationItem]
    total_exposure: Decimal


class RatingDistributionItem(CamelSchema):
    """Exposure aggregated by internal credit rating."""

    rating: str
    exposure: Decimal
    count: int
    percent_of_portfolio: Decimal


class RatingDistributionResponse(CamelSchema):
    items: list[RatingDistributionItem]
    total_exposure: Decimal


class LimitBreachItem(CamelSchema):
    """A counterparty in NEAR_LIMIT or BREACHED state."""

    counterparty_id: str
    counterparty_name: str
    counterparty_type: CounterpartyType

    total_exposure: Decimal
    limit_amount: Decimal
    utilization_percent: Decimal
    status: LimitStatus
    severity: BreachSeverity

    is_infrastructure: bool = False


class LimitBreachResponse(CamelSchema):
    items: list[LimitBreachItem]
    near_limit_count: int
    breached_count: int
