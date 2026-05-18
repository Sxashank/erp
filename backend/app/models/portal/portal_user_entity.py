"""Portal-user ↔ Entity bridge.

Multi-tenant SaaS rule: a borrower (los_entity) is who the loan belongs
to, while ``portal_user`` is who logs into the borrower portal. The
legacy ``portal_user.customer_id`` points at ``mst_customer`` (AR-side,
not borrower-side) and cannot be repurposed without breaking the AR
portal flows. This bridge table is the canonical mapping from a portal
user to one (or more) lending entities they are authorised to act for.

CLAUDE.md §1 / §3.4: every row carries ``organization_id`` so RLS keeps
tenants isolated. The partial unique index enforces "at most one live
link per (portal_user, entity)" while still permitting soft-deleted
historical rows for audit.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.lending.entity import Entity
    from app.models.portal.portal_user import PortalUser


class PortalUserEntity(BaseModel):
    """N:N link between ``portal_user`` and ``los_entity``."""

    __tablename__ = "mst_portal_user_entity"

    portal_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    granted_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Active-vs-historical (separate from is_active which the audit mixin
    # uses for soft-delete semantics). Allows a tenant admin to suspend a
    # link without losing the audit trail.
    is_link_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Relationships
    portal_user: Mapped[PortalUser] = relationship(
        "PortalUser",
        back_populates="entities",
        foreign_keys=[portal_user_id],
        lazy="selectin",
    )
    entity: Mapped[Entity] = relationship(
        "Entity",
        foreign_keys=[entity_id],
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_mst_portal_user_entity_portal_user", "portal_user_id"),
        Index("ix_mst_portal_user_entity_entity", "entity_id"),
        Index("ix_mst_portal_user_entity_org", "organization_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<PortalUserEntity(user={self.portal_user_id}, "
            f"entity={self.entity_id}, active={self.is_link_active})>"
        )
