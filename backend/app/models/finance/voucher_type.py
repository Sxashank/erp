"""Voucher Type model."""

from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import VoucherClass

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.finance.voucher import Voucher


class VoucherType(BaseModel):
    """Voucher Type master for different types of transactions."""

    __tablename__ = "mst_voucher_type"

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Voucher type code e.g. JV, PV, RV, CV",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Display name e.g. Journal Voucher, Payment Voucher",
    )
    voucher_class: Mapped[VoucherClass] = mapped_column(
        SQLEnum(VoucherClass),
        nullable=False,
        comment="Classification - JOURNAL, PAYMENT, RECEIPT, CONTRA, SALES, PURCHASE",
    )
    prefix: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Voucher number prefix e.g. JV-, PV-",
    )
    auto_numbering: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Auto-generate voucher numbers",
    )
    starting_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Starting number for auto-numbering",
    )
    current_number: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Last used number",
    )
    number_format: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Number format pattern e.g. {PREFIX}{YEAR}-{NUMBER:05d}",
    )
    requires_approval: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Requires approval workflow",
    )
    approval_levels: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Number of approval levels required",
    )
    default_narration: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Default narration template",
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="System-defined type (cannot be deleted)",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
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
        back_populates="voucher_types",
        lazy="selectin",
    )
    vouchers: Mapped[List["Voucher"]] = relationship(
        "Voucher",
        back_populates="voucher_type",
        lazy="noload",
    )

    def get_next_number(self, financial_year_code: str) -> str:
        """Generate next voucher number."""
        self.current_number += 1
        if self.number_format:
            return self.number_format.format(
                PREFIX=self.prefix,
                YEAR=financial_year_code,
                NUMBER=self.current_number,
            )
        return f"{self.prefix}{financial_year_code}-{self.current_number:05d}"

    def __repr__(self) -> str:
        return f"<VoucherType(code={self.code}, name={self.name})>"
