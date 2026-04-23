"""Audit Log model for MCA-compliant field-level change tracking.

Per MCA April 2023 notification, this table captures:
- All changes to transaction records
- Old and new values for each field
- User who made the change
- Timestamp and request metadata

This table is IMMUTABLE - no UPDATE or DELETE operations allowed.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import Index, String, Text, DateTime, func, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EntityType(str, Enum):
    """Types of entities that can be audited."""
    VOUCHER = "VOUCHER"
    PURCHASE_BILL = "PURCHASE_BILL"
    SALES_INVOICE = "SALES_INVOICE"
    PAYMENT = "PAYMENT"
    VENDOR = "VENDOR"
    CUSTOMER = "CUSTOMER"
    ACCOUNT = "ACCOUNT"
    JOURNAL_ENTRY = "JOURNAL_ENTRY"
    FIXED_ASSET = "FIXED_ASSET"
    ASSET_CATEGORY = "ASSET_CATEGORY"
    DEPRECIATION_RUN = "DEPRECIATION_RUN"
    # Approval workflow entities
    APPROVAL_WORKFLOW = "APPROVAL_WORKFLOW"
    APPROVAL_REQUEST = "APPROVAL_REQUEST"
    # Lease entities
    LEASE = "LEASE"
    LEASE_MODIFICATION = "LEASE_MODIFICATION"
    LEASE_PAYMENT = "LEASE_PAYMENT"
    # Insurance entities
    INSURANCE_POLICY = "INSURANCE_POLICY"
    INSURANCE_CLAIM = "INSURANCE_CLAIM"
    # Maintenance entities
    AMC_CONTRACT = "AMC_CONTRACT"
    MAINTENANCE_REQUEST = "MAINTENANCE_REQUEST"
    # Configuration entities
    FA_CONFIGURATION = "FA_CONFIGURATION"


class AuditAction(str, Enum):
    """Types of actions that can be audited."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    APPROVE = "APPROVE"
    CANCEL = "CANCEL"
    POST = "POST"
    REVERSE = "REVERSE"
    VOID = "VOID"
    # Fixed Asset specific actions
    CAPITALIZE = "CAPITALIZE"
    DISPOSE = "DISPOSE"
    TRANSFER = "TRANSFER"
    REVALUE = "REVALUE"
    IMPAIR = "IMPAIR"
    # Approval workflow actions
    SUBMIT_FOR_APPROVAL = "SUBMIT_FOR_APPROVAL"
    APPROVAL_APPROVED = "APPROVAL_APPROVED"
    APPROVAL_REJECTED = "APPROVAL_REJECTED"
    APPROVAL_RETURNED = "APPROVAL_RETURNED"
    APPROVAL_ESCALATED = "APPROVAL_ESCALATED"
    # GL-related actions
    GL_POST_SUCCESS = "GL_POST_SUCCESS"
    GL_POST_FAILED = "GL_POST_FAILED"
    # Lease actions
    LEASE_ACTIVATE = "LEASE_ACTIVATE"
    LEASE_TERMINATE = "LEASE_TERMINATE"
    LEASE_MODIFY = "LEASE_MODIFY"
    LEASE_PAYMENT = "LEASE_PAYMENT"
    # Insurance actions
    CLAIM_FILE = "CLAIM_FILE"
    CLAIM_SETTLE = "CLAIM_SETTLE"
    # Configuration actions
    CONFIG_UPDATE = "CONFIG_UPDATE"
    # Bulk operation actions
    BULK_IMPORT = "BULK_IMPORT"
    BULK_UPDATE = "BULK_UPDATE"
    BULK_TRANSFER = "BULK_TRANSFER"
    BULK_DISPOSE = "BULK_DISPOSE"


class AuditLog(Base):
    """MCA-compliant audit trail for all transactions.

    This model stores field-level change history for compliance with
    MCA April 2023 notification requirements.

    IMPORTANT: This table should be made immutable at database level
    by revoking UPDATE and DELETE permissions.
    """

    __tablename__ = "txn_audit_log"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Entity identification
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )

    entity_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Human-readable reference (voucher number, invoice number, etc.)",
    )

    # Action details
    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Who and when
    changed_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        comment="User ID who made the change",
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Change details (JSONB for flexibility)
    old_values: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Previous field values before change",
    )

    new_values: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="New field values after change",
    )

    changed_fields: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
        comment="List of field names that were changed",
    )

    # Optional justification
    change_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User-provided justification for the change",
    )

    # Financial and contextual metadata
    audit_context: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional context: financial impact, GL entries, approval chain, etc.",
    )

    # Request metadata
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    __table_args__ = (
        Index('ix_audit_entity', 'entity_type', 'entity_id'),
        Index('ix_audit_org_timestamp', 'organization_id', 'changed_at'),
        Index('ix_audit_changed_by', 'changed_by'),
        {
            'comment': 'MCA-compliant audit trail - IMMUTABLE table'
        }
    )

    def __repr__(self) -> str:
        return f"<AuditLog({self.entity_type}:{self.entity_id} {self.action} by {self.changed_by})>"
