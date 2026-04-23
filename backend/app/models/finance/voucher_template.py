"""Voucher Template model for reusable voucher entries."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.finance.voucher_type import VoucherType


class VoucherTemplate(BaseModel):
    """
    Voucher Template for reusable voucher entries.

    Unlike Recurring Vouchers, templates don't have scheduling.
    They're used to quickly create common voucher entries.
    """

    __tablename__ = "fin_voucher_template"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    voucher_type_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_voucher_type.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    template_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Name of the voucher template",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Description of when to use this template",
    )
    default_narration: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Default narration for vouchers created from this template",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Total debit/credit amount (for display)",
    )
    template_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Voucher line items as JSON [{account_id, debit, credit, narration}]",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )
    usage_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Number of times this template has been used",
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this template was last used",
    )
    is_favorite: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is marked as a favorite template",
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Category for grouping templates (e.g., PAYROLL, RENT, TAX)",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    voucher_type: Mapped["VoucherType"] = relationship(
        "VoucherType",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<VoucherTemplate(name={self.template_name})>"
