"""Item Category model for Inventory module."""

from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization


class ItemCategory(BaseModel):
    """Item category master for classifying inventory items."""

    __tablename__ = "mst_item_category"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "category_code", name="uq_item_category_org_code"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic Info
    category_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Unique code within organization",
    )
    category_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Hierarchy
    parent_category_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_item_category.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Parent category for hierarchical structure",
    )

    # Settings
    is_stockable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether items in this category are stocked",
    )
    requires_serial_number: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether items require serial number tracking",
    )
    requires_batch_number: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether items require batch number tracking",
    )

    # GL Account Mapping
    gl_inventory_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Inventory GL account",
    )
    gl_expense_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Expense GL account for consumption",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    parent_category: Mapped[Optional["ItemCategory"]] = relationship(
        "ItemCategory",
        remote_side="ItemCategory.id",
        lazy="selectin",
    )
    children: Mapped[List["ItemCategory"]] = relationship(
        "ItemCategory",
        back_populates="parent_category",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ItemCategory(code={self.category_code}, name={self.category_name})>"
