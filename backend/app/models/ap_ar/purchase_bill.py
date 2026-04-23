"""Purchase Bill model."""

import enum
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class BillStatus(str, enum.Enum):
    """Bill status enum."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    """Payment status enum."""
    UNPAID = "UNPAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"


class SupplyType(str, enum.Enum):
    """GST supply type enum."""
    INTRA_STATE = "INTRA_STATE"
    INTER_STATE = "INTER_STATE"


if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.masters.unit import Unit
    from app.models.ap_ar.vendor import Vendor
    from app.models.finance.voucher import Voucher
    from app.models.finance.account import Account
    from app.models.gst.gst_rate import GSTRate
    from app.models.workflow import WorkflowInstance


class PurchaseBill(BaseModel):
    """Purchase Bill header - Vendor Invoice."""

    __tablename__ = "txn_purchase_bill"

    # Bill Info
    bill_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    vendor_invoice_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    vendor_invoice_date: Mapped[Optional["Date"]] = mapped_column(
        Date,
        nullable=True,
    )
    bill_date: Mapped["Date"] = mapped_column(
        Date,
        nullable=False,
    )
    due_date: Mapped[Optional["Date"]] = mapped_column(
        Date,
        nullable=True,
    )

    # References
    vendor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_vendor.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
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
    )

    # Amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    taxable_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    cgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    sgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    igst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    cess_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    tds_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    round_off: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    balance_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # GST Details
    is_reverse_charge: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    supply_type: Mapped[Optional[SupplyType]] = mapped_column(
        Enum(SupplyType),
        nullable=True,
    )
    vendor_gstin: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
    )
    place_of_supply: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
    )

    # Status
    status: Mapped[BillStatus] = mapped_column(
        Enum(BillStatus),
        nullable=False,
        default=BillStatus.DRAFT,
        index=True,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.UNPAID,
    )

    # GL Integration
    voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_posted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Notes
    narration: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Workflow
    workflow_instance_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_instance.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    vendor: Mapped["Vendor"] = relationship(
        "Vendor",
        foreign_keys=[vendor_id],
        lazy="selectin",
    )
    organization: Mapped["Organization"] = relationship(
        "Organization",
        foreign_keys=[organization_id],
        lazy="selectin",
    )
    unit: Mapped[Optional["Unit"]] = relationship(
        "Unit",
        foreign_keys=[unit_id],
        lazy="selectin",
    )
    voucher: Mapped[Optional["Voucher"]] = relationship(
        "Voucher",
        foreign_keys=[voucher_id],
        lazy="selectin",
    )
    workflow_instance: Mapped[Optional["WorkflowInstance"]] = relationship(
        "WorkflowInstance",
        foreign_keys=[workflow_instance_id],
        lazy="selectin",
    )
    lines: Mapped[List["PurchaseBillLine"]] = relationship(
        "PurchaseBillLine",
        back_populates="bill",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<PurchaseBill(number={self.bill_number}, vendor={self.vendor_id})>"


class PurchaseBillLine(BaseModel):
    """Purchase Bill line item."""

    __tablename__ = "txn_purchase_bill_line"

    # Parent
    bill_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_purchase_bill.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Item Details
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    hsn_sac_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("1"),
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Discount
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # Amounts
    taxable_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # GST
    gst_rate_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_gst_rate.id", ondelete="SET NULL"),
        nullable=True,
    )
    cgst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )
    cgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    sgst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )
    sgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    igst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )
    igst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    cess_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )
    cess_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # Total
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # Account
    expense_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    bill: Mapped["PurchaseBill"] = relationship(
        "PurchaseBill",
        back_populates="lines",
        lazy="selectin",
    )
    gst_rate: Mapped[Optional["GSTRate"]] = relationship(
        "GSTRate",
        foreign_keys=[gst_rate_id],
        lazy="selectin",
    )
    expense_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[expense_account_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseBillLine(bill={self.bill_id}, line={self.line_number})>"
