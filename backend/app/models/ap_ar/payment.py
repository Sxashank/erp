"""Payment Entry Model with allocations for vendor payments and customer receipts."""

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.masters.unit import Unit
    from app.models.auth.user import User
    from app.models.finance.account import Account
    from app.models.finance.voucher import Voucher
    from app.models.ap_ar.vendor import Vendor
    from app.models.ap_ar.customer import Customer
    from app.models.tds.tds_section import TDSSection
    from app.models.workflow import WorkflowInstance


class PaymentType(str, enum.Enum):
    """Type of payment transaction."""
    VENDOR_PAYMENT = "VENDOR_PAYMENT"
    CUSTOMER_RECEIPT = "CUSTOMER_RECEIPT"
    ADVANCE_PAYMENT = "ADVANCE_PAYMENT"
    ADVANCE_RECEIPT = "ADVANCE_RECEIPT"
    REFUND_PAYMENT = "REFUND_PAYMENT"
    REFUND_RECEIPT = "REFUND_RECEIPT"


class PartyType(str, enum.Enum):
    """Type of party in the transaction."""
    VENDOR = "VENDOR"
    CUSTOMER = "CUSTOMER"


class PaymentMode(str, enum.Enum):
    """Mode of payment."""
    CASH = "CASH"
    CHEQUE = "CHEQUE"
    NEFT = "NEFT"
    RTGS = "RTGS"
    IMPS = "IMPS"
    UPI = "UPI"
    BANK_TRANSFER = "BANK_TRANSFER"
    DEMAND_DRAFT = "DEMAND_DRAFT"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"


class PaymentStatus(str, enum.Enum):
    """Status of payment entry."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"


class ChequeStatus(str, enum.Enum):
    """Status of cheque if payment mode is cheque."""
    ISSUED = "ISSUED"
    DEPOSITED = "DEPOSITED"
    CLEARED = "CLEARED"
    BOUNCED = "BOUNCED"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"


class DocumentType(str, enum.Enum):
    """Type of document being allocated against."""
    PURCHASE_BILL = "PURCHASE_BILL"
    SALES_INVOICE = "SALES_INVOICE"
    DEBIT_NOTE = "DEBIT_NOTE"
    CREDIT_NOTE = "CREDIT_NOTE"
    ADVANCE = "ADVANCE"


class Payment(BaseModel):
    """Payment/Receipt transaction model."""

    __tablename__ = "txn_payment"

    # Basic Info
    payment_number: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    payment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    payment_type: Mapped[PaymentType] = mapped_column(
        Enum(PaymentType), nullable=False, index=True
    )

    # Party Info
    party_type: Mapped[PartyType] = mapped_column(
        Enum(PartyType), nullable=False, index=True
    )
    vendor_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("mst_vendor.id"), nullable=True, index=True
    )
    customer_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("mst_customer.id"), nullable=True, index=True
    )

    # Organization & Unit
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_organization.id"), nullable=False, index=True
    )
    unit_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("mst_unit.id"), nullable=True
    )

    # Payment Details
    payment_mode: Mapped[PaymentMode] = mapped_column(
        Enum(PaymentMode), nullable=False
    )
    bank_account_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("mst_account.id"), nullable=True
    )
    cash_account_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("mst_account.id"), nullable=True
    )

    # Amounts
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )
    tds_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )
    tds_section_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("mst_tds_section.id"), nullable=True
    )
    tds_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )
    write_off_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )
    currency_code: Mapped[str] = mapped_column(
        String(3), nullable=False, default="INR"
    )
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(12, 6), nullable=False, default=Decimal("1.000000")
    )

    # Cheque Details
    cheque_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    cheque_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cheque_bank_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cheque_branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cheque_status: Mapped[Optional[ChequeStatus]] = mapped_column(
        Enum(ChequeStatus), nullable=True
    )
    cheque_cleared_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cheque_bounced_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cheque_bounced_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Transaction Reference
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # UTR/Transaction ID
    narration: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status & Workflow
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name='txnpaymentstatus', create_type=False),
        nullable=False, default=PaymentStatus.DRAFT, index=True
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    submitted_by_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("mst_user.id"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_by_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("mst_user.id"), nullable=True
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_by_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("mst_user.id"), nullable=True
    )
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # GL Integration
    voucher_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("txn_voucher.id"), nullable=True
    )
    is_posted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    posted_by_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("mst_user.id"), nullable=True
    )

    # Workflow Integration
    workflow_instance_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("wf_workflow_instance.id"), nullable=True, index=True
    )

    # Relationships
    vendor: Mapped[Optional["Vendor"]] = relationship(
        "Vendor", back_populates="payments", lazy="selectin"
    )
    customer: Mapped[Optional["Customer"]] = relationship(
        "Customer", back_populates="payments", lazy="selectin"
    )
    organization: Mapped["Organization"] = relationship(
        "Organization", lazy="selectin"
    )
    unit: Mapped[Optional["Unit"]] = relationship("Unit", lazy="selectin")
    bank_account: Mapped[Optional["Account"]] = relationship(
        "Account", foreign_keys=[bank_account_id], lazy="selectin"
    )
    cash_account: Mapped[Optional["Account"]] = relationship(
        "Account", foreign_keys=[cash_account_id], lazy="selectin"
    )
    tds_section: Mapped[Optional["TDSSection"]] = relationship(
        "TDSSection", lazy="selectin"
    )
    voucher: Mapped[Optional["Voucher"]] = relationship("Voucher", lazy="selectin")
    workflow_instance: Mapped[Optional["WorkflowInstance"]] = relationship(
        "WorkflowInstance", lazy="selectin"
    )
    submitted_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[submitted_by_id], lazy="selectin"
    )
    approved_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[approved_by_id], lazy="selectin"
    )
    cancelled_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[cancelled_by_id], lazy="selectin"
    )
    posted_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[posted_by_id], lazy="selectin"
    )

    # Allocations
    allocations: Mapped[list["PaymentAllocation"]] = relationship(
        "PaymentAllocation",
        back_populates="payment",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_txn_payment_org_date", "organization_id", "payment_date"),
        Index("ix_txn_payment_party", "party_type", "vendor_id", "customer_id"),
        CheckConstraint(
            "(party_type = 'VENDOR' AND vendor_id IS NOT NULL AND customer_id IS NULL) OR "
            "(party_type = 'CUSTOMER' AND customer_id IS NOT NULL AND vendor_id IS NULL)",
            name="ck_payment_party_consistency"
        ),
        CheckConstraint(
            "(payment_mode = 'CASH' AND cash_account_id IS NOT NULL) OR "
            "(payment_mode != 'CASH' AND bank_account_id IS NOT NULL)",
            name="ck_payment_account_mode"
        ),
    )

    def __repr__(self) -> str:
        return f"<Payment {self.payment_number}>"

    @property
    def party_name(self) -> Optional[str]:
        """Get the party name based on party type."""
        if self.party_type == PartyType.VENDOR and self.vendor:
            return self.vendor.name
        elif self.party_type == PartyType.CUSTOMER and self.customer:
            return self.customer.name
        return None

    @property
    def party_id(self) -> Optional[UUID]:
        """Get the party ID based on party type."""
        if self.party_type == PartyType.VENDOR:
            return self.vendor_id
        return self.customer_id

    @property
    def is_payment(self) -> bool:
        """Check if this is a payment (outgoing money)."""
        return self.payment_type in [
            PaymentType.VENDOR_PAYMENT,
            PaymentType.ADVANCE_PAYMENT,
            PaymentType.REFUND_PAYMENT,
        ]

    @property
    def is_receipt(self) -> bool:
        """Check if this is a receipt (incoming money)."""
        return self.payment_type in [
            PaymentType.CUSTOMER_RECEIPT,
            PaymentType.ADVANCE_RECEIPT,
            PaymentType.REFUND_RECEIPT,
        ]

    @property
    def allocated_amount(self) -> Decimal:
        """Calculate total allocated amount."""
        return sum(alloc.allocated_amount for alloc in self.allocations)

    @property
    def unallocated_amount(self) -> Decimal:
        """Calculate unallocated amount."""
        return self.amount - self.allocated_amount


class PaymentAllocation(BaseModel):
    """Allocation of payment against documents (bills/invoices)."""

    __tablename__ = "txn_payment_allocation"

    payment_id: Mapped[UUID] = mapped_column(
        ForeignKey("txn_payment.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType), nullable=False
    )
    document_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    document_number: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # Snapshot for quick reference
    document_date: Mapped[date] = mapped_column(Date, nullable=False)
    document_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )  # Original document amount
    outstanding_before: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )  # Outstanding before this allocation
    allocated_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    allocation_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Relationships
    payment: Mapped["Payment"] = relationship(
        "Payment", back_populates="allocations", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_payment_allocation_doc", "document_type", "document_id"),
        CheckConstraint(
            "allocated_amount > 0",
            name="ck_allocation_positive_amount"
        ),
    )

    def __repr__(self) -> str:
        return f"<PaymentAllocation {self.document_number}: {self.allocated_amount}>"
