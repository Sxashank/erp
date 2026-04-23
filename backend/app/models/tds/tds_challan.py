"""TDS Challan model for aggregating TDS payments."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID
import enum

from sqlalchemy import Date, Numeric, String, Text, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.tds.tds_section import TDSSection
    from app.models.tds.tds_entry import TDSEntry
    from app.models.masters.organization import Organization
    from app.models.finance.financial_year import FinancialYear


class ChallanStatus(str, enum.Enum):
    """Challan payment status."""
    DRAFT = "DRAFT"  # Not yet finalized
    PENDING = "PENDING"  # Ready for payment
    PAID = "PAID"  # Paid but not verified
    VERIFIED = "VERIFIED"  # Verified with bank
    CANCELLED = "CANCELLED"  # Cancelled


class ChallanType(str, enum.Enum):
    """TDS Challan form type."""
    FORM_281 = "281"  # TDS on salary and other than salary


class TDSChallan(BaseModel):
    """
    TDS Challan for aggregating TDS entries for payment.

    A challan aggregates multiple TDS entries for a given section and period
    for deposit to the government.
    """

    __tablename__ = "txn_tds_challan"

    # Challan identification
    challan_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        unique=True,
        index=True,
        comment="Challan Identification Number (CIN) after payment",
    )
    bsr_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="BSR code of the bank branch",
    )
    serial_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Serial number from bank receipt",
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # TDS Section
    tds_section_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_tds_section.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="TDS section for this challan",
    )

    # Period
    financial_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_financial_year.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assessment_year: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Assessment year e.g. 2024-25",
    )
    period_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Start of deduction period covered",
    )
    period_to: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="End of deduction period covered",
    )

    # Amounts (aggregated from TDS entries)
    total_base_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Total base amount on which TDS was deducted",
    )
    total_tds_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Total basic TDS amount",
    )
    total_surcharge: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Total surcharge",
    )
    total_cess: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Total health & education cess",
    )
    interest_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Interest for late payment (if any)",
    )
    penalty_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Penalty amount (if any)",
    )
    other_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Other charges/adjustments",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Total challan amount (TDS + Surcharge + Cess + Interest + Penalty)",
    )

    # Entry count
    entry_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Number of TDS entries in this challan",
    )

    # Payment details
    status: Mapped[ChallanStatus] = mapped_column(
        SQLEnum(ChallanStatus),
        nullable=False,
        default=ChallanStatus.DRAFT,
        index=True,
    )
    payment_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date of payment to bank",
    )
    payment_mode: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Payment mode: ONLINE, CHEQUE, DD",
    )
    bank_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Bank through which payment made",
    )
    bank_branch: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Bank branch",
    )
    bank_account_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Bank account number used for payment",
    )
    cheque_dd_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Cheque/DD number (if applicable)",
    )
    cheque_dd_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Cheque/DD date (if applicable)",
    )

    # OLTAS details (Online Tax Accounting System)
    oltas_acknowledgment: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="OLTAS acknowledgment number",
    )
    oltas_status: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="OLTAS verification status",
    )
    oltas_verified_at: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Challan form details
    challan_type: Mapped[ChallanType] = mapped_column(
        SQLEnum(ChallanType),
        nullable=False,
        default=ChallanType.FORM_281,
    )
    minor_head: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Minor head code (200 for company, 400 for individual)",
    )

    # Deductor details (organization)
    deductor_tan: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="TAN of deductor (organization)",
    )
    deductor_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Name of deductor (organization)",
    )
    deductor_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Return filing reference
    return_quarter: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Quarter for return: Q1, Q2, Q3, Q4",
    )
    is_included_in_return: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this challan is included in a TDS return",
    )
    return_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Reference to TDS return if included",
    )

    # Additional details
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional data for reporting",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    tds_section: Mapped["TDSSection"] = relationship(
        "TDSSection",
        lazy="selectin",
    )
    financial_year: Mapped["FinancialYear"] = relationship(
        "FinancialYear",
        lazy="selectin",
    )
    entries: Mapped[List["TDSEntry"]] = relationship(
        "TDSEntry",
        back_populates="challan",
        lazy="selectin",
    )

    @property
    def is_late(self) -> bool:
        """Check if challan payment is late (beyond 7th of next month)."""
        if not self.payment_date:
            return True
        # TDS should be deposited by 7th of next month
        from datetime import timedelta
        due_date = date(
            self.period_to.year + (1 if self.period_to.month == 12 else 0),
            1 if self.period_to.month == 12 else self.period_to.month + 1,
            7,
        )
        return self.payment_date > due_date

    def __repr__(self) -> str:
        return f"<TDSChallan(number={self.challan_number}, amount={self.total_amount})>"
