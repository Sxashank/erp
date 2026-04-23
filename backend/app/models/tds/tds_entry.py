"""TDS Entry model for tracking TDS deductions."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Date, Numeric, String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import TDSDeducteeType, TDSChallanStatus

if TYPE_CHECKING:
    from app.models.tds.tds_section import TDSSection
    from app.models.tds.tds_challan import TDSChallan
    from app.models.finance.voucher import Voucher
    from app.models.masters.organization import Organization
    from app.models.ap_ar.vendor import Vendor
    from app.models.finance.financial_year import FinancialYear


class TDSEntry(BaseModel):
    """TDS Entry for tracking tax deductions at source."""

    __tablename__ = "txn_tds_entry"

    tds_section_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_tds_section.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Source voucher for this TDS entry",
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Vendor reference for aggregate threshold tracking
    vendor_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_vendor.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Vendor for aggregate TDS threshold tracking",
    )
    # Financial year for aggregate tracking
    financial_year_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_financial_year.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Financial year for aggregate threshold tracking",
    )
    # Threshold tracking fields
    is_threshold_crossed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="True if this entry crossed single/aggregate threshold",
    )
    aggregate_amount_ytd: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Running aggregate amount for vendor in this FY at time of entry",
    )
    threshold_reason: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Reason for TDS: SINGLE_THRESHOLD, AGGREGATE_THRESHOLD, MANUAL",
    )
    # Deductee details
    deductee_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Name of deductee (vendor/party)",
    )
    deductee_pan: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="PAN of deductee",
    )
    deductee_type: Mapped[TDSDeducteeType] = mapped_column(
        SQLEnum(TDSDeducteeType),
        nullable=False,
        default=TDSDeducteeType.COMPANY,
    )
    deductee_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    # TDS calculation
    deduction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Date of TDS deduction",
    )
    base_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Amount on which TDS is calculated",
    )
    tds_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="TDS rate applied",
    )
    tds_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Basic TDS amount",
    )
    surcharge: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Surcharge amount",
    )
    cess: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Health & Education Cess",
    )
    total_tds: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Total TDS = TDS + Surcharge + Cess",
    )
    # Lower deduction certificate
    lower_deduction_cert_no: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Lower deduction certificate number",
    )
    # Challan reference (for grouped challan payment)
    challan_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_tds_challan.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Reference to grouped TDS challan",
    )
    # Challan details (legacy individual fields)
    challan_status: Mapped[TDSChallanStatus] = mapped_column(
        SQLEnum(TDSChallanStatus),
        nullable=False,
        default=TDSChallanStatus.PENDING,
    )
    challan_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="BSR/Challan number after payment",
    )
    challan_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date of TDS deposit",
    )
    bank_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Bank through which TDS deposited",
    )
    bsr_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="BSR code of the bank",
    )
    # Certificate details
    certificate_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="TDS certificate number (Form 16/16A)",
    )
    certificate_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    # Return filing
    return_quarter: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Quarter for return e.g. Q1, Q2, Q3, Q4",
    )
    return_filed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="Is TDS return filed for this entry",
    )
    acknowledgment_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="TDS return acknowledgment number",
    )
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    tds_section: Mapped["TDSSection"] = relationship(
        "TDSSection",
        lazy="selectin",
    )
    voucher: Mapped[Optional["Voucher"]] = relationship(
        "Voucher",
        lazy="selectin",
    )
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    vendor: Mapped[Optional["Vendor"]] = relationship(
        "Vendor",
        lazy="selectin",
    )
    financial_year: Mapped[Optional["FinancialYear"]] = relationship(
        "FinancialYear",
        lazy="selectin",
    )
    challan: Mapped[Optional["TDSChallan"]] = relationship(
        "TDSChallan",
        back_populates="entries",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<TDSEntry(deductee={self.deductee_name}, amount={self.total_tds})>"
