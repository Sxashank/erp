"""Audit hash-chain anchor persistence (STAGE-5-PENDING-002 closure).

CLAUDE.md §8.5: a daily anchor over the ordered audit rows for a calendar
day, seeded from the previous day's anchor. Tampering with any historical
row surfaces as a hash mismatch at that day and every subsequent day.

The actual hashing is pure math in `app.core.audit_hash_chain`. This
module is the persistence contract.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditDayAnchor(Base):
    """One row per (organization_id, day) — the canonical SHA-256 anchor.

    Written by the daily `compute_audit_anchors_job` (APScheduler, 00:15 IST)
    and verified on demand by the `/api/v1/audit/verify-chain` admin
    endpoint.
    """

    __tablename__ = "audit_day_anchor"
    __table_args__ = (
        Index(
            "ix_audit_day_anchor_org_day",
            "organization_id",
            "day",
            unique=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Tenant scope. NULL = system-global anchor (login/auth).",
    )
    day: Mapped[date] = mapped_column(Date, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_anchor: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Hex SHA-256 anchor from the prior day (genesis = 64 zeros)",
    )
    anchor: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Hex SHA-256 anchor for this day",
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AuditDayAnchor org={self.organization_id} day={self.day} anchor={self.anchor[:8]}…>"
