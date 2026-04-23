"""GST Rate model."""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Numeric, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class GSTRate(BaseModel):
    """GST Rate master for tax rate configurations."""

    __tablename__ = "mst_gst_rate"

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Rate code e.g. GST0, GST5, GST12, GST18, GST28",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Rate name e.g. GST 18%",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Description of the rate applicability",
    )
    rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Total GST rate percentage",
    )
    cgst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Central GST rate (intra-state)",
    )
    sgst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="State GST rate (intra-state)",
    )
    igst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Integrated GST rate (inter-state)",
    )
    cess_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Compensation cess rate",
    )
    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Rate effective from date",
    )
    effective_to: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Rate effective to date (null = currently active)",
    )
    is_composition: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Is this a composition scheme rate",
    )
    is_reverse_charge: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Is this applicable for reverse charge",
    )

    def __repr__(self) -> str:
        return f"<GSTRate(code={self.code}, rate={self.rate}%)>"
