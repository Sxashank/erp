"""Fund-utilization category master.

A scheme-scoped lookup of eligible end-use categories for the loan
amount (e.g. land acquisition, plant & machinery, IDC). The IIF claim
form requires the borrower to break the requested loan amount down by
these categories.

``organization_id`` is nullable for the same reason as
``SubventionScheme`` — seeded platform-wide rows are inherited, but a
tenant may override.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class FundUtilizationCategory(BaseModel):
    """Eligible end-use bucket under a subvention scheme."""

    __tablename__ = "mst_fund_utilization_category"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "scheme_id",
            "code",
            name="uq_mst_fuc_org_scheme_code",
        ),
        Index("ix_mst_fuc_org", "organization_id"),
        Index("ix_mst_fuc_scheme", "scheme_id"),
        Index("ix_mst_fuc_code", "code"),
    )

    organization_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=True,
    )
    scheme_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_subvention_scheme.id", ondelete="CASCADE"),
        nullable=True,
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
