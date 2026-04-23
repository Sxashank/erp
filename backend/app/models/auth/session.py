"""User session model for refresh token management."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.auth.user import User


class UserSession(BaseModel):
    """User session for tracking refresh tokens."""

    __tablename__ = "txn_user_session"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Token tracking
    refresh_token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    token_family: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # Session info
    device_info: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )

    # Timestamps
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Revocation
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_reason: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="sessions",
        foreign_keys=[user_id],
    )

    @property
    def is_valid(self) -> bool:
        """Check if session is valid (not expired and not revoked)."""
        if self.is_revoked:
            return False
        from datetime import timezone
        return datetime.now(timezone.utc) < self.expires_at

    def revoke(self, reason: str = "manual") -> None:
        """Revoke this session."""
        from datetime import timezone
        self.is_revoked = True
        self.revoked_at = datetime.now(timezone.utc)
        self.revoked_reason = reason

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"
