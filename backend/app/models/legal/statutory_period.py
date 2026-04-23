"""Statutory Period management models.

Provides comprehensive tracking of legal limitation periods
and statutory deadlines under Indian law.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.legal.enums import AlertPriority

if TYPE_CHECKING:
    from app.models.lending.collections import LegalCase


class StatutoryPeriod(BaseModel):
    """Master table for statutory periods under Indian law.

    Defines the various limitation periods and statutory
    timelines for different legal actions.
    """

    __tablename__ = "mst_statutory_period"
    __table_args__ = (
        Index("ix_statutory_period_org", "organization_id"),
        Index("ix_statutory_period_provision", "provision_code"),
        UniqueConstraint(
            "organization_id", "provision_code", name="uq_statutory_provision"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
    )

    # Provision Details
    provision_code: Mapped[str] = mapped_column(String(50), nullable=False)
    provision_name: Mapped[str] = mapped_column(String(200), nullable=False)
    act_name: Mapped[str] = mapped_column(String(200), nullable=False)
    section_reference: Mapped[str] = mapped_column(String(100), nullable=False)

    # Period Details
    period_days: Mapped[int] = mapped_column(Integer, nullable=False)
    period_months: Mapped[Optional[int]] = mapped_column(Integer)
    period_years: Mapped[Optional[int]] = mapped_column(Integer)
    period_description: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # "60 days", "3 years"

    # Calculation Rules
    start_event: Mapped[str] = mapped_column(
        String(200), nullable=False
    )  # "Notice receipt", "Cause of action"
    includes_holidays: Mapped[bool] = mapped_column(
        Boolean, default=True
    )  # Whether to include holidays
    extension_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    extension_grounds: Mapped[Optional[str]] = mapped_column(Text)

    # Consequence of Non-compliance
    consequence: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # "Time-barred", "Loss of right"

    # Applicable Forums
    applicable_forums: Mapped[Optional[dict]] = mapped_column(JSONB)
    applicable_case_types: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Alert Configuration
    alert_before_days: Mapped[Optional[dict]] = mapped_column(
        JSONB
    )  # [30, 15, 7, 1] days before

    # Reference
    legal_reference: Mapped[Optional[str]] = mapped_column(Text)  # Citation, precedents

    description: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    trackings: Mapped[List["PeriodTracking"]] = relationship(
        back_populates="statutory_period"
    )


class PeriodTracking(BaseModel):
    """Active period tracking for legal cases.

    Tracks active statutory periods for each case
    with calculated deadlines.
    """

    __tablename__ = "txn_period_tracking"
    __table_args__ = (
        Index("ix_period_track_org", "organization_id"),
        Index("ix_period_track_case", "legal_case_id"),
        Index("ix_period_track_period", "statutory_period_id"),
        Index("ix_period_track_deadline", "deadline_date"),
        Index("ix_period_track_status", "status"),
        UniqueConstraint(
            "legal_case_id",
            "statutory_period_id",
            "start_date",
            name="uq_case_period_tracking",
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
    )

    # Foreign Keys
    legal_case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("col_legal_case.id"),
        nullable=False,
    )
    statutory_period_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_statutory_period.id"),
        nullable=False,
    )
    loan_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id"),
    )

    # Period Details
    period_name: Mapped[str] = mapped_column(String(200), nullable=False)
    provision_reference: Mapped[str] = mapped_column(String(200), nullable=False)

    # Dates
    trigger_event: Mapped[str] = mapped_column(
        String(200), nullable=False
    )  # What triggered this period
    trigger_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )  # When the trigger occurred
    start_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )  # When period starts counting
    deadline_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_days: Mapped[int] = mapped_column(Integer, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default="ACTIVE"
    )  # ACTIVE, COMPLIED, EXPIRED, EXTENDED, NA

    # Compliance
    action_required: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # What action needs to be taken
    action_taken_date: Mapped[Optional[date]] = mapped_column(Date)
    action_taken_details: Mapped[Optional[str]] = mapped_column(Text)
    compliance_verified_by: Mapped[Optional[str]] = mapped_column(String(200))
    compliance_verified_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Extension
    is_extended: Mapped[bool] = mapped_column(Boolean, default=False)
    extension_reason: Mapped[Optional[str]] = mapped_column(Text)
    extended_deadline: Mapped[Optional[date]] = mapped_column(Date)
    extension_approved_by: Mapped[Optional[str]] = mapped_column(String(200))

    # Days Remaining (calculated field)
    days_remaining: Mapped[Optional[int]] = mapped_column(Integer)
    last_calculated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Alert Status
    alert_priority: Mapped[Optional[AlertPriority]] = mapped_column(String(20))
    last_alert_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    statutory_period: Mapped["StatutoryPeriod"] = relationship(
        back_populates="trackings"
    )
    legal_case: Mapped["LegalCase"] = relationship()
    alerts: Mapped[List["LimitationAlert"]] = relationship(
        back_populates="period_tracking",
        cascade="all, delete-orphan",
    )


class LimitationAlert(BaseModel):
    """Alerts for approaching limitation deadlines.

    Generates and tracks alerts for statutory deadlines
    to ensure timely compliance.
    """

    __tablename__ = "txn_limitation_alert"
    __table_args__ = (
        Index("ix_limit_alert_tracking", "period_tracking_id"),
        Index("ix_limit_alert_priority", "priority"),
        Index("ix_limit_alert_status", "status"),
        Index("ix_limit_alert_date", "alert_date"),
    )

    # Foreign Keys
    period_tracking_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_period_tracking.id"),
        nullable=False,
    )

    # Alert Details
    alert_date: Mapped[date] = mapped_column(Date, nullable=False)
    alert_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # SCHEDULED, REMINDER, ESCALATION, FINAL

    # Priority & Status
    priority: Mapped[AlertPriority] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING"
    )  # PENDING, SENT, ACKNOWLEDGED, ACTIONED

    # Content
    alert_title: Mapped[str] = mapped_column(String(200), nullable=False)
    alert_message: Mapped[str] = mapped_column(Text, nullable=False)
    days_to_deadline: Mapped[int] = mapped_column(Integer, nullable=False)

    # Recipients
    recipients: Mapped[Optional[dict]] = mapped_column(
        JSONB
    )  # List of user IDs/emails

    # Delivery
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sent_via: Mapped[Optional[str]] = mapped_column(String(50))  # EMAIL, SMS, SYSTEM
    delivery_status: Mapped[Optional[str]] = mapped_column(String(50))

    # Acknowledgement
    acknowledged_by_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    acknowledged_by_name: Mapped[Optional[str]] = mapped_column(String(200))
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Action Taken
    action_taken: Mapped[Optional[str]] = mapped_column(Text)
    action_taken_by_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    action_taken_by_name: Mapped[Optional[str]] = mapped_column(String(200))
    action_taken_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Escalation
    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    escalated_to: Mapped[Optional[str]] = mapped_column(String(200))
    escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    period_tracking: Mapped["PeriodTracking"] = relationship(back_populates="alerts")
