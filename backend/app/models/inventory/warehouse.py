"""Warehouse model for Inventory module."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID
from enum import Enum

from sqlalchemy import (
    Boolean,
    ForeignKey,
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
    from app.models.masters.unit import Unit


class WarehouseType(str, Enum):
    """Type of warehouse/storage location."""
    MAIN = "MAIN"
    BRANCH = "BRANCH"
    TRANSIT = "TRANSIT"
    VIRTUAL = "VIRTUAL"


class Warehouse(BaseModel):
    """Warehouse/Storage location master."""

    __tablename__ = "mst_warehouse"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "warehouse_code", name="uq_warehouse_org_code"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Unit/Branch Association
    unit_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_unit.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Associated branch/unit",
    )

    # Basic Info
    warehouse_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Unique code within organization",
    )
    warehouse_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    warehouse_type: Mapped[WarehouseType] = mapped_column(
        SQLEnum(WarehouseType),
        default=WarehouseType.MAIN,
        nullable=False,
    )

    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    address_line2: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    pincode: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )

    # Contact
    contact_person: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    contact_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    contact_email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Settings
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Default warehouse for the organization",
    )
    allow_negative_stock: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    unit: Mapped[Optional["Unit"]] = relationship(
        "Unit",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Warehouse(code={self.warehouse_code}, name={self.warehouse_name})>"
