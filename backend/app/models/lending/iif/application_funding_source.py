"""Application-level source-of-funds rows for scheme loan tagging."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ApplicationFundingSource(BaseModel):
    """One source-of-funds row for a portal scheme application."""

    __tablename__ = "los_application_funding_source"
    __table_args__ = (
        UniqueConstraint(
            "application_id",
            "source_code",
            name="uq_los_application_funding_source_app_code",
        ),
        Index("ix_los_application_funding_source_org", "organization_id"),
        Index("ix_los_application_funding_source_app", "application_id"),
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
    source_code: Mapped[str] = mapped_column(String(50), nullable=False)
    source_label: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    remarks: Mapped[str | None] = mapped_column(String(500), nullable=True)
