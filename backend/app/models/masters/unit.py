"""Unit (Branch/Location) master model."""

from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import UnitType, EntityStatus

if TYPE_CHECKING:
    from app.models.auth.user import User
    from app.models.auth.role import UserRole
    from app.models.masters.organization import Organization


class Unit(BaseModel):
    """Unit master - branches, offices, locations."""

    __tablename__ = "mst_unit"

    # Basic info
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    short_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Type & Hierarchy
    unit_type: Mapped[str] = mapped_column(
        String(30),
        default=UnitType.BRANCH.value,
        nullable=False,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_unit_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_unit.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        index=True,
    )

    # Accounting
    is_separate_accounting: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # GST Registration
    gstin: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
    )
    gst_state_code: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
    )

    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    address_line2: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    district: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    state_code: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
    )
    pincode: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    country: Mapped[str] = mapped_column(
        String(50),
        default="India",
        nullable=False,
    )

    # Contact
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    manager_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=EntityStatus.ACTIVE.value,
        nullable=False,
        index=True,
    )
    is_head_office: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="units",
    )
    parent_unit: Mapped[Optional["Unit"]] = relationship(
        "Unit",
        remote_side="Unit.id",
        back_populates="child_units",
    )
    child_units: Mapped[List["Unit"]] = relationship(
        "Unit",
        back_populates="parent_unit",
        lazy="selectin",
    )
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="default_unit",
        foreign_keys="User.default_unit_id",
        lazy="selectin",
    )
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="unit",
        foreign_keys="[UserRole.unit_id]",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Unit(code={self.code}, name={self.name})>"
