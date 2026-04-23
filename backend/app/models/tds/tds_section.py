"""TDS Section model."""

from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import Date, Numeric, String, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TDSSection(BaseModel):
    """TDS Section master for Income Tax sections and rates."""

    __tablename__ = "mst_tds_section"

    section_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Section code e.g. 194C, 194J, 194I",
    )
    section_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Section description",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of applicability",
    )
    # Rates for different deductee types
    rate_individual: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("10.00"),
        comment="Rate for Individual/HUF with PAN",
    )
    rate_company: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("10.00"),
        comment="Rate for Company with PAN",
    )
    rate_no_pan: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("20.00"),
        comment="Rate when PAN not available",
    )
    rate_lower_deduction: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Lower deduction rate if applicable",
    )
    # Threshold limits
    threshold_single: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Single transaction threshold",
    )
    threshold_annual: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Annual aggregate threshold",
    )
    # TCS section flag
    is_tcs: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Is this a TCS section (not TDS)",
    )
    # Surcharge and cess
    surcharge_applicable: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Is surcharge applicable",
    )
    cess_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("4.00"),
        comment="Health & Education Cess rate",
    )
    # Surcharge configuration per deductee type and amount slab
    # Format: [{"min": 0, "max": 10000000, "rates": {"INDIVIDUAL": 0, "COMPANY": 0}},
    #          {"min": 10000000, "max": 100000000, "rates": {"INDIVIDUAL": 0.10, "COMPANY": 0.02}}]
    surcharge_slabs: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Surcharge rate slabs by amount and deductee type",
    )
    # Effective dates
    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Section effective from date",
    )
    effective_to: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Section effective to date (null = currently active)",
    )
    # Return form
    return_form: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="26Q",
        comment="TDS return form - 24Q, 26Q, 27Q, 27EQ",
    )
    # Nature of payment code for TDS return
    nature_of_payment_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Code for TDS return filing",
    )

    def __repr__(self) -> str:
        return f"<TDSSection(code={self.section_code}, rate={self.rate_individual}%)>"
