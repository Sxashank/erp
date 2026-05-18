"""Per-application fund-utilization line items.

For each ``LoanApplication``, a list of rows that break the requested
loan amount down by ``FundUtilizationCategory``. The service layer
enforces ``SUM(amounts) == application.requested_amount`` at submit
time (±0.01 tolerance for rounding).
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.lending.iif.fund_utilization_category import (
        FundUtilizationCategory,
    )


class ApplicationUtilization(BaseModel):
    """One row per (application, category) breaking the requested amount."""

    __tablename__ = "los_application_utilization"
    __table_args__ = (
        UniqueConstraint(
            "application_id",
            "category_id",
            name="uq_los_application_utilization_app_cat",
        ),
        Index("ix_los_application_utilization_org", "organization_id"),
        Index("ix_los_application_utilization_app", "application_id"),
        Index("ix_los_application_utilization_cat", "category_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_application.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_fund_utilization_category.id", ondelete="RESTRICT"),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    # Lender-approved amount per category — set at sanction time. Sum
    # must match LoanSanction.sanctioned_amount (±0.01) once any line
    # carries a value. Nullable while the breakdown is still pending.
    approved_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    remarks: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Lazy-loaded; the service uses ``selectinload(..., .category)`` for
    # bulk fetches so the FE response can include ``categoryLabel``.
    category: Mapped[FundUtilizationCategory] = relationship(
        "FundUtilizationCategory",
        foreign_keys=[category_id],
        lazy="raise",
    )
