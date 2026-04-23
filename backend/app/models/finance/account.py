"""Account (Ledger) model for Chart of Accounts."""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import AccountType, ControlAccountType, BalanceType

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.finance.account_group import AccountGroup


class Account(BaseModel):
    """Account/Ledger master for Chart of Accounts."""

    __tablename__ = "mst_account"

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Account code e.g. 1001, 2001",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Account name e.g. Cash in Hand, Trade Payables",
    )
    account_group_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account_group.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Parent account group",
    )
    account_type: Mapped[AccountType] = mapped_column(
        SQLEnum(AccountType),
        nullable=False,
        default=AccountType.LEDGER,
        comment="Type of account - GROUP, LEDGER, BANK, CASH, CONTROL",
    )
    is_control_account: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Is this a control account for sub-ledger",
    )
    control_type: Mapped[Optional[ControlAccountType]] = mapped_column(
        SQLEnum(ControlAccountType),
        nullable=True,
        comment="Type of control account if is_control_account is True",
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        default="INR",
        nullable=False,
        comment="Currency code ISO 4217",
    )
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Opening balance amount",
    )
    opening_balance_type: Mapped[Optional[BalanceType]] = mapped_column(
        SQLEnum(BalanceType),
        nullable=True,
        comment="Opening balance type DR/CR",
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Current running balance",
    )
    current_balance_type: Mapped[Optional[BalanceType]] = mapped_column(
        SQLEnum(BalanceType),
        nullable=True,
        comment="Current balance type DR/CR",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    gstin: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
        comment="GSTIN if applicable",
    )
    pan: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="PAN if applicable",
    )
    tds_applicable: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Is TDS applicable on this account",
    )
    tds_section: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Default TDS section code",
    )
    is_bank_account: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    bank_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    bank_account_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    bank_ifsc_code: Mapped[Optional[str]] = mapped_column(
        String(11),
        nullable=True,
    )
    bank_branch: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    is_cash_account: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    allow_negative_balance: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_reconciliation_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Is bank reconciliation required for this account",
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="System-defined account (cannot be deleted)",
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
        back_populates="accounts",
        lazy="selectin",
    )
    account_group: Mapped["AccountGroup"] = relationship(
        "AccountGroup",
        back_populates="accounts",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Account(code={self.code}, name={self.name})>"
