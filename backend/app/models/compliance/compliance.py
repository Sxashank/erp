"""
Compliance Models

Models for regulatory compliance tracking and management.
"""

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, Date, DateTime,
    Numeric, ForeignKey, Enum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class RegulatoryBody(str, enum.Enum):
    """Regulatory bodies for compliance"""
    RBI = "RBI"  # Reserve Bank of India
    SEBI = "SEBI"  # Securities and Exchange Board of India
    MCA = "MCA"  # Ministry of Corporate Affairs
    GST = "GST"  # Goods and Services Tax
    INCOME_TAX = "INCOME_TAX"  # Income Tax Department
    EPFO = "EPFO"  # Employees' Provident Fund Organisation
    ESIC = "ESIC"  # Employees' State Insurance Corporation
    STATE = "STATE"  # State-level compliance
    OTHER = "OTHER"


class ComplianceFrequency(str, enum.Enum):
    """Frequency of compliance"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    HALF_YEARLY = "HALF_YEARLY"
    ANNUALLY = "ANNUALLY"
    AS_REQUIRED = "AS_REQUIRED"
    ONE_TIME = "ONE_TIME"


class ComplianceStatus(str, enum.Enum):
    """Status of compliance instance"""
    NOT_DUE = "NOT_DUE"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    PREPARED = "PREPARED"
    UNDER_REVIEW = "UNDER_REVIEW"
    FILED = "FILED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    DELAYED = "DELAYED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class CompliancePriority(str, enum.Enum):
    """Priority levels for compliance"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ComplianceItem(BaseModel):
    """
    Master table for compliance requirements.
    Defines what needs to be complied with.
    """
    __tablename__ = "compliance_item"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("mst_organization.id"), nullable=False)

    # Basic Information
    item_code = Column(String(30), nullable=False)
    item_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Regulatory Details
    regulatory_body = Column(
        Enum(RegulatoryBody, name="regulatorybody", create_type=False),
        nullable=False
    )
    regulation_reference = Column(String(100), nullable=True)  # e.g., "RBI Circular No. XYZ"
    section_reference = Column(String(100), nullable=True)  # e.g., "Section 45IA"

    # Frequency & Timing
    frequency = Column(
        Enum(ComplianceFrequency, name="compliancefrequency", create_type=False),
        nullable=False,
        default=ComplianceFrequency.MONTHLY
    )
    due_day = Column(Integer, nullable=True)  # Day of month/quarter for due date
    due_month = Column(Integer, nullable=True)  # Month for annual filings
    grace_days = Column(Integer, nullable=False, default=0)  # Days after due date before penalty

    # Priority & Penalty
    priority = Column(
        Enum(CompliancePriority, name="compliancepriority", create_type=False),
        nullable=False,
        default=CompliancePriority.MEDIUM
    )
    penalty_type = Column(String(50), nullable=True)  # FIXED, PERCENTAGE, DAILY
    penalty_amount = Column(Numeric(18, 2), nullable=True)
    penalty_rate_per_day = Column(Numeric(10, 4), nullable=True)

    # Responsible Parties
    responsible_designation = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)

    # Document Requirements
    required_documents = Column(JSONB, nullable=True)  # List of required document types
    form_name = Column(String(50), nullable=True)  # e.g., "GSTR-1", "Form 26Q"
    filing_portal = Column(String(200), nullable=True)  # URL of filing portal

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)

    # Audit
    created_by = Column(UUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)

    # Relationships
    organization = relationship("Organization", foreign_keys=[organization_id])
    instances = relationship("ComplianceInstance", back_populates="compliance_item")

    __table_args__ = (
        UniqueConstraint('organization_id', 'item_code', name='uq_compliance_item_org_code'),
        Index('ix_compliance_item_org', 'organization_id'),
        Index('ix_compliance_item_body', 'regulatory_body'),
    )


class ComplianceInstance(BaseModel):
    """
    Instance of a compliance requirement for a specific period.
    Tracks the actual filing/submission.
    """
    __tablename__ = "compliance_instance"

    compliance_item_id = Column(UUID(as_uuid=True), ForeignKey("compliance_item.id"), nullable=False)

    # Period Information
    period_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=True)  # For monthly/quarterly
    period_quarter = Column(Integer, nullable=True)  # 1-4 for quarterly
    period_from = Column(Date, nullable=True)
    period_to = Column(Date, nullable=True)

    # Due Date Management
    original_due_date = Column(Date, nullable=False)
    extended_due_date = Column(Date, nullable=True)
    actual_due_date = Column(Date, nullable=False)  # Computed: extended or original

    # Status Tracking
    status = Column(
        Enum(ComplianceStatus, name="compliancestatus", create_type=False),
        nullable=False,
        default=ComplianceStatus.PENDING
    )

    # Filing Details
    filed_date = Column(Date, nullable=True)
    acknowledgment_number = Column(String(100), nullable=True)
    acknowledgment_date = Column(Date, nullable=True)
    reference_number = Column(String(100), nullable=True)

    # Delay & Penalty
    is_delayed = Column(Boolean, nullable=False, default=False)
    delay_days = Column(Integer, nullable=True)
    penalty_paid = Column(Numeric(18, 2), nullable=True)
    penalty_reference = Column(String(100), nullable=True)

    # Assignment
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)
    reviewer = Column(UUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)

    # Documents & Notes
    documents = Column(JSONB, nullable=True)  # List of attached documents
    remarks = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)

    # Reminder Settings
    reminder_days = Column(Integer, nullable=True)  # Days before due to send reminder
    last_reminder_sent = Column(DateTime(timezone=True), nullable=True)

    # Audit
    prepared_by = Column(UUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)
    prepared_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    filed_by = Column(UUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)

    # Relationships
    compliance_item = relationship("ComplianceItem", back_populates="instances")
    assignee = relationship("User", foreign_keys=[assigned_to])
    preparer = relationship("User", foreign_keys=[prepared_by])
    reviewer_user = relationship("User", foreign_keys=[reviewed_by])
    filer = relationship("User", foreign_keys=[filed_by])

    __table_args__ = (
        UniqueConstraint(
            'compliance_item_id', 'period_year', 'period_month', 'period_quarter',
            name='uq_compliance_instance_period'
        ),
        Index('ix_compliance_instance_item', 'compliance_item_id'),
        Index('ix_compliance_instance_status', 'status'),
        Index('ix_compliance_instance_due', 'actual_due_date'),
    )


class ComplianceDocument(BaseModel):
    """
    Documents attached to compliance instances.
    """
    __tablename__ = "compliance_document"

    instance_id = Column(UUID(as_uuid=True), ForeignKey("compliance_instance.id", ondelete="CASCADE"), nullable=False)

    document_type = Column(String(50), nullable=False)  # FORM, PROOF, ACKNOWLEDGMENT, etc.
    document_name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)

    uploaded_at = Column(DateTime(timezone=True), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    remarks = Column(Text, nullable=True)

    # Relationships
    instance = relationship("ComplianceInstance")
    uploader = relationship("User", foreign_keys=[uploaded_by])

    __table_args__ = (
        Index('ix_compliance_document_instance', 'instance_id'),
    )


class ComplianceReminder(BaseModel):
    """
    Reminders sent for compliance instances.
    """
    __tablename__ = "compliance_reminder"

    instance_id = Column(UUID(as_uuid=True), ForeignKey("compliance_instance.id", ondelete="CASCADE"), nullable=False)

    reminder_type = Column(String(50), nullable=False)  # EMAIL, SMS, IN_APP
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)
    recipient_email = Column(String(200), nullable=True)

    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)

    sent_at = Column(DateTime(timezone=True), nullable=False)
    delivery_status = Column(String(20), nullable=True)  # SENT, DELIVERED, FAILED

    # Relationships
    instance = relationship("ComplianceInstance")
    recipient = relationship("User", foreign_keys=[recipient_id])

    __table_args__ = (
        Index('ix_compliance_reminder_instance', 'instance_id'),
    )
