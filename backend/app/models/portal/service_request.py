"""Portal Service Request Models.

Handles service requests like prepayment, foreclosure, EMI date change, etc.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    Text,
    DateTime,
    Date,
    Numeric,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.portal.enums import (
    ServiceRequestType,
    ServiceRequestStatus,
)


class PortalServiceRequest(BaseModel):
    """Service request from portal.

    Tracks requests for prepayment, foreclosure, EMI date change, etc.
    """

    __tablename__ = "portal_service_request"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("portal_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    loan_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("lms_loan_account.id"),
        nullable=False,
        index=True,
    )

    # Request Info
    request_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    request_type: Mapped[ServiceRequestType] = mapped_column(nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Status
    status: Mapped[ServiceRequestStatus] = mapped_column(
        default=ServiceRequestStatus.DRAFT
    )
    status_message: Mapped[Optional[str]] = mapped_column(String(500))

    # Prepayment/Foreclosure specific
    requested_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    quote_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    quote_valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime)
    quote_breakdown: Mapped[Optional[str]] = mapped_column(Text)  # JSON

    # EMI Date Change specific
    current_emi_date: Mapped[Optional[int]] = mapped_column()  # Day of month
    requested_emi_date: Mapped[Optional[int]] = mapped_column()
    effective_from: Mapped[Optional[date]] = mapped_column(Date)

    # Address/Contact Change specific
    change_details: Mapped[Optional[str]] = mapped_column(Text)  # JSON

    # Assignment
    assigned_to: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("hris_employee.id")
    )
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    assigned_team: Mapped[Optional[str]] = mapped_column(String(100))

    # Processing
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("hris_employee.id")
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    review_remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Approval
    approval_required: Mapped[bool] = mapped_column(Boolean, default=True)
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("hris_employee.id")
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(500))

    # Payment (if charges applicable)
    charges_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    charges_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    payment_request_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("portal_payment_request.id")
    )
    payment_status: Mapped[Optional[str]] = mapped_column(String(50))

    # Completion
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("hris_employee.id")
    )
    completion_remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Cancellation
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancelled_by: Mapped[Optional[UUID]] = mapped_column()
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(500))

    # SLA
    sla_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_sla_breached: Mapped[bool] = mapped_column(Boolean, default=False)

    # Customer Feedback
    customer_rating: Mapped[Optional[int]] = mapped_column()  # 1-5
    customer_feedback: Mapped[Optional[str]] = mapped_column(Text)
    feedback_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    documents: Mapped[List["PortalServiceRequestDocument"]] = relationship(
        "PortalServiceRequestDocument",
        back_populates="service_request",
        cascade="all, delete-orphan",
    )
    history: Mapped[List["PortalServiceRequestHistory"]] = relationship(
        "PortalServiceRequestHistory",
        back_populates="service_request",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_portal_sr_user_status", "user_id", "status"),
        Index("ix_portal_sr_org_status", "organization_id", "status"),
        Index("ix_portal_sr_loan", "loan_account_id", "request_type"),
        Index("ix_portal_sr_assigned", "assigned_to", "status"),
    )


class PortalServiceRequestDocument(BaseModel):
    """Documents attached to service request.

    Supporting documents uploaded by customer or generated by system.
    """

    __tablename__ = "portal_service_request_document"

    service_request_id: Mapped[UUID] = mapped_column(
        ForeignKey("portal_service_request.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Document Info
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # ID_PROOF, ADDRESS_PROOF, etc.
    description: Mapped[Optional[str]] = mapped_column(String(500))

    # File Info
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64))

    # Upload Info
    uploaded_by: Mapped[str] = mapped_column(
        String(20), default="CUSTOMER"
    )  # CUSTOMER, SYSTEM, EMPLOYEE
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("hris_employee.id")
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    verification_remarks: Mapped[Optional[str]] = mapped_column(String(500))

    # Relationships
    service_request: Mapped["PortalServiceRequest"] = relationship(
        "PortalServiceRequest", back_populates="documents"
    )

    __table_args__ = (
        Index("ix_portal_sr_doc_request", "service_request_id"),
    )


class PortalServiceRequestHistory(BaseModel):
    """Service request status history.

    Tracks all status changes with timestamps and remarks.
    """

    __tablename__ = "portal_service_request_history"

    service_request_id: Mapped[UUID] = mapped_column(
        ForeignKey("portal_service_request.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status Change
    from_status: Mapped[Optional[ServiceRequestStatus]] = mapped_column()
    to_status: Mapped[ServiceRequestStatus] = mapped_column(nullable=False)
    change_reason: Mapped[Optional[str]] = mapped_column(String(500))
    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Who made the change
    changed_by_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # CUSTOMER, EMPLOYEE, SYSTEM
    changed_by_id: Mapped[Optional[UUID]] = mapped_column()
    changed_by_name: Mapped[Optional[str]] = mapped_column(String(100))

    # Timestamp
    changed_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # Additional Info
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    service_request: Mapped["PortalServiceRequest"] = relationship(
        "PortalServiceRequest", back_populates="history"
    )

    __table_args__ = (
        Index("ix_portal_sr_history_request", "service_request_id", "changed_at"),
    )
