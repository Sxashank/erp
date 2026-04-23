"""Line Item History model for tracking changes to transaction line items.

This captures changes to individual line items within transactions,
linked to the parent AuditLog entry.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Index, String, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LineItemEntityType(str, Enum):
    """Types of line item entities."""
    VOUCHER_LINE = "VOUCHER_LINE"
    BILL_LINE = "BILL_LINE"
    INVOICE_LINE = "INVOICE_LINE"
    PAYMENT_ALLOCATION = "PAYMENT_ALLOCATION"


class LineItemAction(str, Enum):
    """Actions on line items."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class LineItemHistory(Base):
    """Track changes to transaction line items.

    Links to parent AuditLog entry to group all line item changes
    that occurred as part of a single transaction update.
    """

    __tablename__ = "txn_line_item_history"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Link to parent audit log entry
    parent_audit_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_audit_log.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line item identification
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    line_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        comment="Original line item ID",
    )

    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Line number within the transaction",
    )

    # Action on this line
    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Change details
    old_values: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    new_values: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship to parent audit log
    parent_audit = relationship(
        "AuditLog",
        backref="line_item_changes",
        foreign_keys=[parent_audit_id],
    )

    __table_args__ = (
        Index('ix_line_history_parent', 'parent_audit_id'),
        Index('ix_line_history_line', 'entity_type', 'line_id'),
        {
            'comment': 'Line item change history - linked to parent audit log'
        }
    )

    def __repr__(self) -> str:
        return f"<LineItemHistory({self.entity_type}:{self.line_id} {self.action})>"
