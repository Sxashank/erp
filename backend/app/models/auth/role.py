"""Role and Permission models for RBAC."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import BaseModel, AuditMixin

if TYPE_CHECKING:
    from app.models.auth.user import User
    from app.models.masters.unit import Unit


class Permission(BaseModel):
    """Permission definition model."""

    __tablename__ = "mst_permission"

    code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    module: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    resource: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Relationships
    role_permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="permission",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Permission(code={self.code})>"


class Role(BaseModel):
    """Role definition model."""

    __tablename__ = "mst_role"

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    is_system_role: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    role_permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="role",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="role",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def permissions(self) -> List[Permission]:
        """Get list of permissions for this role."""
        return [rp.permission for rp in self.role_permissions]

    @property
    def permission_codes(self) -> List[str]:
        """Get list of permission codes for this role."""
        return [rp.permission.code for rp in self.role_permissions]

    def __repr__(self) -> str:
        return f"<Role(code={self.code})>"


class RolePermission(Base, AuditMixin):
    """Junction table for Role-Permission many-to-many relationship."""

    __tablename__ = "map_role_permission"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_role.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_permission.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="role_permissions",
    )
    permission: Mapped["Permission"] = relationship(
        "Permission",
        back_populates="role_permissions",
    )


class UserRole(Base, AuditMixin):
    """Junction table for User-Role many-to-many relationship with unit scope."""

    __tablename__ = "map_user_role"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "unit_id", name="uq_user_role_unit"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_role.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unit_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_unit.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Validity period
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    effective_to: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="user_roles",
        foreign_keys=[user_id],
    )
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="user_roles",
    )
    unit: Mapped[Optional["Unit"]] = relationship(
        "Unit",
        back_populates="user_roles",
        foreign_keys=[unit_id],
    )

    @property
    def is_valid(self) -> bool:
        """Check if the role assignment is currently valid."""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        if self.effective_from > now:
            return False
        if self.effective_to and self.effective_to < now:
            return False
        return True
