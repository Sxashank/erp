"""General Ledger Entry model for GL posting audit trail."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import BalanceType, PartyType, GLEntryType, GLEntrySourceType

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.finance.voucher import Voucher, VoucherLine
    from app.models.finance.account import Account
    from app.models.finance.financial_year import FinancialYear, FinancialPeriod


GL_ENTRY_TYPE_ENUM = PGEnum(
    GLEntryType,
    name="gl_entry_type",
    create_type=False,
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)

GL_ENTRY_SOURCE_TYPE_ENUM = PGEnum(
    GLEntrySourceType,
    name="gl_entry_source_type",
    create_type=False,
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)

PARTY_TYPE_ENUM = PGEnum(
    PartyType,
    name="party_type",
    create_type=False,
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class GLEntry(BaseModel):
    """
    General Ledger Entry - Individual debit/credit posting record.

    This is the immutable audit trail of all GL transactions. Each voucher line
    posting creates one GLEntry. Reversals create opposite entries rather than
    modifying existing ones.
    """

    __tablename__ = "txn_gl_entry"

    # Reference to source voucher
    voucher_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Source voucher ID",
    )
    voucher_line_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher_line.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Source voucher line ID",
    )
    voucher_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Denormalized voucher number for quick search",
    )
    voucher_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Voucher/Transaction date",
    )

    # Entry type and source
    entry_type: Mapped[GLEntryType] = mapped_column(
        GL_ENTRY_TYPE_ENUM,
        nullable=False,
        default=GLEntryType.NORMAL,
        comment="Type of GL entry - NORMAL, REVERSAL, OPENING, CLOSING, ADJUSTMENT",
    )
    source_type: Mapped[GLEntrySourceType] = mapped_column(
        GL_ENTRY_SOURCE_TYPE_ENUM,
        nullable=False,
        default=GLEntrySourceType.MANUAL,
        comment="Source of this entry",
    )
    source_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Reference to source document (bill/invoice/receipt number)",
    )
    source_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="ID of source document (purchase_bill.id, sales_invoice.id, etc.)",
    )

    # Account information
    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="GL Account ID",
    )
    account_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Denormalized account code for reporting",
    )
    account_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Denormalized account name for reporting",
    )

    # Entry amounts
    debit_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Debit amount (positive means debit)",
    )
    credit_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Credit amount (positive means credit)",
    )
    balance_type: Mapped[BalanceType] = mapped_column(
        SQLEnum(
            BalanceType,
            name="balance_type",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        comment="DR or CR indicating the side of this entry",
    )

    # Currency (for multi-currency support)
    currency_code: Mapped[str] = mapped_column(
        String(3),
        default="INR",
        nullable=False,
        comment="Currency code ISO 4217",
    )
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        default=Decimal("1.000000"),
        nullable=False,
        comment="Exchange rate to base currency",
    )
    base_debit_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Debit in base currency (INR)",
    )
    base_credit_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Credit in base currency (INR)",
    )

    # Party/Sub-ledger information
    party_type: Mapped[Optional[PartyType]] = mapped_column(
        PARTY_TYPE_ENUM,
        nullable=True,
        comment="Type of party - CUSTOMER, VENDOR, EMPLOYEE",
    )
    party_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Party ID for sub-ledger tracking",
    )
    party_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Denormalized party name for reporting",
    )

    # Cost center
    cost_center_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Cost center ID for expense allocation",
    )
    cost_center_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Denormalized cost center code",
    )

    # Period information
    financial_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_financial_year.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    period_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_financial_period.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Narration
    narration: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Entry narration/description",
    )

    # Reference details
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="External reference (cheque no, UTR, etc.)",
    )
    reference_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Reversal tracking
    is_reversed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Has this entry been reversed",
    )
    reversal_entry_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_gl_entry.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID of the reversal entry (if reversed)",
    )
    original_entry_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_gl_entry.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID of original entry (if this is a reversal)",
    )
    reversal_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date when entry was reversed",
    )

    # Posting information
    posting_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Date/time when entry was posted to GL",
    )
    posted_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="User who posted this entry",
    )

    # Running balance (for account statement)
    running_balance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment="Running balance after this entry (for statements)",
    )
    running_balance_type: Mapped[Optional[BalanceType]] = mapped_column(
        SQLEnum(
            BalanceType,
            name="balance_type",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=True,
        comment="Running balance type DR/CR",
    )

    # Additional metadata
    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sequential entry number for this account in period",
    )
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional metadata for reporting/analytics",
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unit_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_unit.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    voucher: Mapped["Voucher"] = relationship(
        "Voucher",
        foreign_keys=[voucher_id],
        lazy="selectin",
    )
    voucher_line: Mapped[Optional["VoucherLine"]] = relationship(
        "VoucherLine",
        foreign_keys=[voucher_line_id],
        lazy="selectin",
    )
    account: Mapped["Account"] = relationship(
        "Account",
        foreign_keys=[account_id],
        lazy="selectin",
    )
    financial_year: Mapped["FinancialYear"] = relationship(
        "FinancialYear",
        foreign_keys=[financial_year_id],
        lazy="selectin",
    )
    period: Mapped["FinancialPeriod"] = relationship(
        "FinancialPeriod",
        foreign_keys=[period_id],
        lazy="selectin",
    )
    organization: Mapped["Organization"] = relationship(
        "Organization",
        foreign_keys=[organization_id],
        lazy="selectin",
    )

    # Table-level indexes for common queries
    __table_args__ = (
        # Account statement query
        Index("ix_gl_entry_account_date", "account_id", "voucher_date"),
        # Party ledger query
        Index("ix_gl_entry_party", "party_type", "party_id", "voucher_date"),
        # Period-wise reports
        Index("ix_gl_entry_period", "period_id", "account_id"),
        # Cost center reports
        Index("ix_gl_entry_cost_center", "cost_center_id", "voucher_date"),
        # Source document lookup
        Index("ix_gl_entry_source", "source_type", "source_id"),
        # Organization partition
        Index("ix_gl_entry_org_account", "organization_id", "account_id"),
        # Financial year rollup
        Index("ix_gl_entry_fy_account", "financial_year_id", "account_id"),
    )

    @property
    def amount(self) -> Decimal:
        """Get the entry amount (non-zero value)."""
        return self.debit_amount if self.debit_amount > 0 else self.credit_amount

    @property
    def signed_amount(self) -> Decimal:
        """Get signed amount (positive for debit, negative for credit)."""
        if self.debit_amount > 0:
            return self.debit_amount
        return -self.credit_amount

    def __repr__(self) -> str:
        return f"<GLEntry(voucher={self.voucher_number}, account={self.account_code}, dr={self.debit_amount}, cr={self.credit_amount})>"
