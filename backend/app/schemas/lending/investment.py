"""Treasury investment portfolio schemas.

Wire format is camelCase per ``CamelSchema`` so the frontend can consume
fields directly (CLAUDE.md §5.4). Money fields stay ``Decimal`` in Python
and serialise to JSON strings (Pydantic v2 default) per CLAUDE.md §6.2.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.base import CamelSchema, PaginatedResponse

# =============================================================================
# Create / Mutate
# =============================================================================


class InvestmentCreateRequest(CamelSchema):
    """Payload for POST /treasury/investments.

    Accepts both snake_case and camelCase keys (``populate_by_name=True``).
    Numeric strings are coerced to ``Decimal`` by Pydantic v2.
    """

    type: str = Field(..., max_length=30)
    category: str = Field(..., max_length=10)
    issuer: str = Field(..., max_length=200, min_length=1)
    description: str = Field(..., max_length=500, min_length=1)
    isin: str | None = Field(None, max_length=20)

    face_value: Decimal = Field(..., gt=0)
    purchase_price: Decimal = Field(..., gt=0)
    # Fractional MF units allowed → 4dp.
    units: Decimal = Field(..., gt=0)

    coupon_rate: Decimal = Field(default=Decimal("0"), ge=0)
    ytm: Decimal = Field(default=Decimal("0"), ge=0)
    coupon_frequency: str = Field(..., max_length=20)

    purchase_date: date
    # Nullable for mutual funds / open-ended schemes.
    maturity_date: date | None = None

    broker: str | None = Field(None, max_length=200)
    remarks: str | None = None


class InvestmentMatureRequest(CamelSchema):
    """Payload for POST /treasury/investments/{id}/mature.

    Two flavours:
      - Natural maturity (sale_value omitted) — proceeds = face_value * units.
      - Pre-maturity sale (sale_value provided) — uses the provided amount.
    """

    sale_value: Decimal | None = Field(default=None, ge=0)
    sale_date: date | None = None
    remarks: str | None = None


# =============================================================================
# Response
# =============================================================================


class InvestmentResponse(CamelSchema):
    """Detail / list-item response for a single investment."""

    id: UUID
    organization_id: UUID
    investment_number: str

    type: str
    category: str

    issuer: str
    description: str
    isin: str | None = None

    face_value: Decimal
    purchase_price: Decimal
    units: Decimal

    coupon_rate: Decimal
    ytm: Decimal
    coupon_frequency: str

    purchase_date: date
    maturity_date: date | None = None

    broker: str | None = None
    remarks: str | None = None

    status: str
    current_value: Decimal | None = None
    accrued_interest: Decimal

    sale_value: Decimal | None = None
    sale_date: date | None = None
    realized_gain_loss: Decimal | None = None

    created_at: datetime
    updated_at: datetime | None = None
    version: int


class InvestmentListResponse(PaginatedResponse):
    """Paginated list response (camelCase items)."""

    items: list[InvestmentResponse]


# =============================================================================
# Portfolio summary
# =============================================================================


class CategoryBreakdown(CamelSchema):
    """One row of the category / type breakdown."""

    key: str
    count: int
    face_value: Decimal
    purchase_value: Decimal
    current_value: Decimal


class PortfolioSummaryResponse(CamelSchema):
    """Aggregate portfolio metrics for the treasury dashboard."""

    total_count: int
    active_count: int
    total_face_value: Decimal
    total_purchase_value: Decimal
    total_current_value: Decimal
    unrealized_gain_loss: Decimal
    weighted_avg_ytm: Decimal | None = None
    by_category: list[CategoryBreakdown] = Field(default_factory=list)
    by_type: list[CategoryBreakdown] = Field(default_factory=list)


# =============================================================================
# Maturity schedule
# =============================================================================


class MaturityBucketItem(CamelSchema):
    """Slim investment record used inside a maturity bucket."""

    id: UUID
    investment_number: str
    issuer: str
    description: str
    type: str
    face_value: Decimal
    units: Decimal
    coupon_rate: Decimal
    maturity_date: date

    @model_validator(mode="before")
    @classmethod
    def _from_orm(cls, obj: Any) -> Any:
        if isinstance(obj, dict):
            return obj
        return {
            "id": obj.id,
            "investment_number": obj.investment_number,
            "issuer": obj.issuer,
            "description": obj.description,
            "type": obj.type,
            "face_value": obj.face_value,
            "units": obj.units,
            "coupon_rate": obj.coupon_rate,
            "maturity_date": obj.maturity_date,
        }


class MaturityBucket(CamelSchema):
    """One bucket on the maturity ladder (typically a month label)."""

    label: str
    period_start: date
    period_end: date
    total_face_value: Decimal
    investment_count: int
    investments: list[MaturityBucketItem] = Field(default_factory=list)


class InvestmentMaturityResponse(CamelSchema):
    """Top-level maturity schedule payload returned by /maturity."""

    months_ahead: int
    as_of_date: date
    upcoming_30d: list[MaturityBucketItem] = Field(default_factory=list)
    total_maturing_30d: Decimal
    total_maturing_90d: Decimal
    total_maturing_period: Decimal
    buckets: list[MaturityBucket] = Field(default_factory=list)
