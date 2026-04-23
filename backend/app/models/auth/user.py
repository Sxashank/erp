"""User model for authentication and authorization."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import UserStatus, AuthType

if TYPE_CHECKING:
    from app.models.auth.role import Role, UserRole
    from app.models.auth.session import UserSession
    from app.models.masters.organization import Organization
    from app.models.masters.unit import Unit


class User(BaseModel):
    """User account model."""

    __tablename__ = "mst_user"

    # Basic info
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    employee_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
    )

    # Authentication
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    auth_type: Mapped[str] = mapped_column(
        String(20),
        default=AuthType.LOCAL.value,
        nullable=False,
    )

    # MFA
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    mfa_secret: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Status & Security
    status: Mapped[str] = mapped_column(
        String(20),
        default=UserStatus.ACTIVE.value,
        nullable=False,
        index=True,
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_login_ip: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Password management
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    password_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    must_change_password: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Organization & Unit
    organization_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="SET NULL"),
        nullable=True,
    )
    default_unit_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_unit.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Profile
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        default="Asia/Kolkata",
        nullable=False,
    )

    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization",
        back_populates="users",
        foreign_keys=[organization_id],
        lazy="selectin",
    )
    default_unit: Mapped[Optional["Unit"]] = relationship(
        "Unit",
        back_populates="users",
        foreign_keys=[default_unit_id],
        lazy="selectin",
    )
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="user",
        foreign_keys="[UserRole.user_id]",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        foreign_keys="[UserSession.user_id]",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def is_locked(self) -> bool:
        """Check if account is locked."""
        if self.locked_until is None:
            return False
        from datetime import timezone
        now = datetime.now(timezone.utc)
        return now < self.locked_until

    @property
    def is_password_expired(self) -> bool:
        """Check if password has expired."""
        if self.password_expires_at is None:
            return False
        from datetime import timezone
        now = datetime.now(timezone.utc)
        return now > self.password_expires_at

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"
