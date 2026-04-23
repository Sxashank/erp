"""Payment Terms model."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PaymentTerms(BaseModel):
    """Payment Terms master for defining payment conditions."""

    __tablename__ = "mst_payment_terms"

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Payment terms code e.g. NET30, IMMEDIATE, COD",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Payment terms name e.g. Net 30 Days",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Description of the payment terms",
    )
    days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of days from invoice date for payment due",
    )
    discount_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Days within which early payment discount applies",
    )
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Early payment discount percentage",
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
        comment="Organization this payment terms belongs to",
    )

    # Relationships
    organization = relationship("Organization", back_populates="payment_terms")

    def __repr__(self) -> str:
        return f"<PaymentTerms(code={self.code}, days={self.days})>"
