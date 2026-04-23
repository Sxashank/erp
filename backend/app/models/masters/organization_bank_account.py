"""Organization Bank Account model."""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.finance.account import Account


class OrganizationBankAccount(BaseModel):
    """Organization Bank Account model for storing bank details."""

    __tablename__ = "mst_organization_bank_account"

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Bank Details
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    account_number: Mapped[str] = mapped_column(String(30), nullable=False)
    ifsc_code: Mapped[str] = mapped_column(String(11), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(200), nullable=False)
    branch_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    branch_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    micr_code: Mapped[Optional[str]] = mapped_column(String(9), nullable=True)
    swift_code: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)

    # Account Classification
    account_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="CURRENT"
    )  # CURRENT, SAVINGS, OD, CC, FIXED_DEPOSIT

    # Ledger Linking
    ledger_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Limits (for OD/CC accounts)
    sanctioned_limit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    drawing_power: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True
    )

    # Flags
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_payments: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_receipts: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="bank_accounts"
    )
    ledger_account: Mapped[Optional["Account"]] = relationship(
        "Account", foreign_keys=[ledger_account_id]
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "account_number", name="uq_org_bank_account_number"
        ),
        Index("ix_org_bank_account_org_active", "organization_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<OrganizationBankAccount {self.account_name} - {self.account_number}>"
