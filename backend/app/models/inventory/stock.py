"""Stock Balance and Transaction models for Inventory module."""

from datetime import datetime, date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID
from enum import Enum

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.inventory.item_master import ItemMaster
    from app.models.inventory.warehouse import Warehouse


class TransactionType(str, Enum):
    """Type of stock transaction."""
    STOCK_IN = "STOCK_IN"
    STOCK_OUT = "STOCK_OUT"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    ADJUSTMENT_PLUS = "ADJUSTMENT_PLUS"
    ADJUSTMENT_MINUS = "ADJUSTMENT_MINUS"
    OPENING_BALANCE = "OPENING_BALANCE"
    RETURN_IN = "RETURN_IN"
    RETURN_OUT = "RETURN_OUT"
    SCRAP = "SCRAP"


class TransactionStatus(str, Enum):
    """Status of stock transaction."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class StockBalance(BaseModel):
    """Current stock balance by item and warehouse."""

    __tablename__ = "txn_stock_balance"
    __table_args__ = (
        UniqueConstraint(
            "item_id", "warehouse_id", name="uq_stock_balance_item_warehouse"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Item & Location
    item_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_item_master.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_warehouse.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Quantities
    quantity_on_hand: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0"),
        nullable=False,
        comment="Physical stock available",
    )
    quantity_reserved: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0"),
        nullable=False,
        comment="Reserved for orders/allocations",
    )
    quantity_in_transit: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0"),
        nullable=False,
        comment="Stock in transit",
    )

    # Value
    average_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0"),
        nullable=False,
        comment="Weighted average cost",
    )
    total_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0"),
        nullable=False,
        comment="Total inventory value",
    )

    # Tracking
    last_transaction_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    item: Mapped["ItemMaster"] = relationship(
        "ItemMaster",
        lazy="selectin",
    )
    warehouse: Mapped["Warehouse"] = relationship(
        "Warehouse",
        lazy="selectin",
    )

    @property
    def available_quantity(self) -> Decimal:
        """Get available quantity (on hand - reserved)."""
        return self.quantity_on_hand - self.quantity_reserved

    def __repr__(self) -> str:
        return f"<StockBalance(item={self.item_id}, warehouse={self.warehouse_id}, qty={self.quantity_on_hand})>"


class StockTransaction(BaseModel):
    """Stock transaction for inventory movements."""

    __tablename__ = "txn_stock_transaction"

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Transaction Reference
    transaction_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Unique transaction reference",
    )
    transaction_type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType),
        nullable=False,
        index=True,
    )
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )
    status: Mapped[TransactionStatus] = mapped_column(
        SQLEnum(TransactionStatus),
        default=TransactionStatus.DRAFT,
        nullable=False,
    )

    # Item & Location
    item_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_item_master.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_warehouse.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Transfer - Destination warehouse (for transfers)
    to_warehouse_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_warehouse.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Destination warehouse for transfers",
    )

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        comment="Transaction quantity (positive)",
    )
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0"),
        nullable=False,
    )
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0"),
        nullable=False,
    )

    # Before/After Balances
    balance_before: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0"),
        nullable=False,
    )
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0"),
        nullable=False,
    )

    # Batch/Serial Tracking
    batch_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    serial_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    expiry_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Reference Documents
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Source document type (PO, SO, GRN, etc.)",
    )
    reference_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Source document ID",
    )
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Source document number",
    )

    # Notes
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Approval
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    item: Mapped["ItemMaster"] = relationship(
        "ItemMaster",
        lazy="selectin",
    )
    warehouse: Mapped["Warehouse"] = relationship(
        "Warehouse",
        foreign_keys=[warehouse_id],
        lazy="selectin",
    )
    to_warehouse: Mapped[Optional["Warehouse"]] = relationship(
        "Warehouse",
        foreign_keys=[to_warehouse_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<StockTransaction(number={self.transaction_number}, type={self.transaction_type})>"
