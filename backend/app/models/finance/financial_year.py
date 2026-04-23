"""Financial Year and Period models."""

from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization


class FinancialYear(BaseModel):
    """Financial Year master table."""

    __tablename__ = "mst_financial_year"

    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="FY code e.g. FY2024-25",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Display name e.g. April 2024 - March 2025",
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Financial year start date",
    )
    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Financial year end date",
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Is this the current active financial year",
    )
    is_closed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Is this financial year closed",
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the year was closed",
    )
    closed_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who closed the year",
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="financial_years",
        lazy="selectin",
    )
    periods: Mapped[List["FinancialPeriod"]] = relationship(
        "FinancialPeriod",
        back_populates="financial_year",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="FinancialPeriod.period_number",
    )

    def __repr__(self) -> str:
        return f"<FinancialYear(code={self.code})>"


class FinancialPeriod(BaseModel):
    """Financial Period (monthly) table."""

    __tablename__ = "mst_financial_period"

    financial_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_financial_year.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Period number 1-12 (or 13 for adjustment period)",
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Period name e.g. April 2024",
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    # Period closing (hard close - no entries allowed)
    is_closed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    closed_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Period locking (soft lock - prevents new entries but allows viewing)
    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Soft lock - prevents new entries but allows viewing",
    )
    locked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the period was locked",
    )
    locked_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who locked the period",
    )
    lock_reason: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="GST_RETURN_FILED, PERIOD_CLOSE, AUDIT, etc.",
    )
    # GST return filing date - entries on or before this date are locked
    gst_return_filed_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date until which GST return has been filed (entries on/before this date locked)",
    )
    is_adjustment_period: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Is this the year-end adjustment period",
    )

    # Relationships
    financial_year: Mapped["FinancialYear"] = relationship(
        "FinancialYear",
        back_populates="periods",
    )

    def __repr__(self) -> str:
        return f"<FinancialPeriod(name={self.name})>"
