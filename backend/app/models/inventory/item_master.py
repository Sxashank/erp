"""Item Master model for Inventory module."""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID
from enum import Enum

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.inventory.item_category import ItemCategory


class UnitOfMeasure(str, Enum):
    """Unit of measure for inventory items."""
    EACH = "EACH"
    BOX = "BOX"
    CARTON = "CARTON"
    PACK = "PACK"
    KG = "KG"
    GRAM = "GRAM"
    LITER = "LITER"
    ML = "ML"
    METER = "METER"
    CM = "CM"
    PIECE = "PIECE"
    SET = "SET"
    PAIR = "PAIR"
    DOZEN = "DOZEN"
    REAM = "REAM"


class ItemType(str, Enum):
    """Type of inventory item."""
    STOCK = "STOCK"
    SERVICE = "SERVICE"
    CONSUMABLE = "CONSUMABLE"
    FIXED_ASSET = "FIXED_ASSET"


class ItemMaster(BaseModel):
    """Item master for inventory items."""

    __tablename__ = "mst_item_master"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "item_code", name="uq_item_master_org_code"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Category
    category_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_item_category.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Basic Info
    item_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Unique item code within organization",
    )
    item_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    item_type: Mapped[ItemType] = mapped_column(
        SQLEnum(ItemType),
        default=ItemType.STOCK,
        nullable=False,
    )
    uom: Mapped[UnitOfMeasure] = mapped_column(
        SQLEnum(UnitOfMeasure),
        default=UnitOfMeasure.EACH,
        nullable=False,
        comment="Primary unit of measure",
    )

    # Specifications
    brand: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    model_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Stock Keeping Unit",
    )
    barcode: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Stock Settings
    is_stockable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    requires_serial_number: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    requires_batch_number: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    shelf_life_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Shelf life in days for perishable items",
    )

    # Inventory Levels
    minimum_stock_level: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0"),
        nullable=False,
        comment="Reorder point",
    )
    maximum_stock_level: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0"),
        nullable=False,
    )
    reorder_quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0"),
        nullable=False,
    )

    # Pricing
    standard_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0"),
        nullable=False,
        comment="Standard cost per unit",
    )
    selling_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0"),
        nullable=False,
    )

    # Tax
    hsn_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="HSN code for GST",
    )
    gst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0"),
        nullable=False,
        comment="GST rate percentage",
    )

    # GL Account Override
    gl_inventory_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Override category inventory account",
    )
    gl_expense_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Override category expense account",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    category: Mapped["ItemCategory"] = relationship(
        "ItemCategory",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ItemMaster(code={self.item_code}, name={self.item_name})>"
