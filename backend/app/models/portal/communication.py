"""Portal Communication Models.

Handles notifications, messages, tickets, and announcements.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    Text,
    DateTime,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.portal.enums import (
    NotificationChannel,
    NotificationPriority,
    TicketStatus,
    TicketPriority,
    TicketCategory,
)


class PortalNotification(BaseModel):
    """Portal notifications.

    Supports in-app, push, SMS, email, and WhatsApp channels.
    """

    __tablename__ = "portal_notification"

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

    # Notification Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # PAYMENT_DUE, PAYMENT_RECEIVED, etc.

    # Delivery
    channel: Mapped[NotificationChannel] = mapped_column(
        default=NotificationChannel.IN_APP
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        default=NotificationPriority.MEDIUM
    )

    # Action
    action_url: Mapped[Optional[str]] = mapped_column(String(500))
    action_data: Mapped[Optional[str]] = mapped_column(Text)  # JSON payload

    # Reference (what triggered the notification)
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # LOAN, PAYMENT, TICKET
    reference_id: Mapped[Optional[UUID]] = mapped_column()

    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivery_status: Mapped[Optional[str]] = mapped_column(String(50))
    delivery_error: Mapped[Optional[str]] = mapped_column(Text)

    # Expiry
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (
        Index("ix_portal_notif_user_read", "user_id", "is_read"),
        Index("ix_portal_notif_user_type", "user_id", "notification_type"),
    )


class PortalMessage(BaseModel):
    """Two-way messages between customer and support.

    Part of a message thread for conversations.
    """

    __tablename__ = "portal_message"

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

    # Thread (for conversation grouping)
    thread_id: Mapped[Optional[UUID]] = mapped_column(index=True)
    parent_message_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("portal_message.id")
    )

    # Message Content
    subject: Mapped[Optional[str]] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Direction
    is_from_customer: Mapped[bool] = mapped_column(Boolean, default=True)
    sender_name: Mapped[Optional[str]] = mapped_column(String(100))
    sender_employee_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("hris_employee.id")
    )

    # Attachments
    has_attachments: Mapped[bool] = mapped_column(Boolean, default=False)
    attachment_ids: Mapped[Optional[str]] = mapped_column(Text)  # JSON array of UUIDs

    # Reference
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # LOAN, TICKET, etc.
    reference_id: Mapped[Optional[UUID]] = mapped_column()

    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    replies: Mapped[List["PortalMessage"]] = relationship(
        "PortalMessage",
        back_populates="parent",
        remote_side="PortalMessage.parent_message_id",
    )
    parent: Mapped[Optional["PortalMessage"]] = relationship(
        "PortalMessage",
        back_populates="replies",
        remote_side="PortalMessage.id",
    )

    __table_args__ = (
        Index("ix_portal_message_thread", "thread_id"),
        Index("ix_portal_message_user_read", "user_id", "is_read"),
    )


class PortalTicket(BaseModel):
    """Support ticket.

    Tracks customer support requests with status workflow.
    """

    __tablename__ = "portal_ticket"

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

    # Ticket Info
    ticket_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Classification
    category: Mapped[TicketCategory] = mapped_column(nullable=False)
    sub_category: Mapped[Optional[str]] = mapped_column(String(100))
    priority: Mapped[TicketPriority] = mapped_column(
        default=TicketPriority.MEDIUM
    )

    # Status
    status: Mapped[TicketStatus] = mapped_column(default=TicketStatus.OPEN)
    status_changed_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # Assignment
    assigned_to: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("hris_employee.id")
    )
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    assigned_team: Mapped[Optional[str]] = mapped_column(String(100))

    # Reference
    loan_account_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("lms_loan_account.id")
    )
    related_payment_id: Mapped[Optional[UUID]] = mapped_column()
    related_service_request_id: Mapped[Optional[UUID]] = mapped_column()

    # Resolution
    resolution_summary: Mapped[Optional[str]] = mapped_column(Text)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolved_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("hris_employee.id"))

    # Closure
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    closed_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("hris_employee.id"))
    closure_reason: Mapped[Optional[str]] = mapped_column(String(255))

    # SLA
    sla_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_sla_breached: Mapped[bool] = mapped_column(Boolean, default=False)

    # Feedback
    customer_rating: Mapped[Optional[int]] = mapped_column()  # 1-5
    customer_feedback: Mapped[Optional[str]] = mapped_column(Text)
    feedback_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (
        Index("ix_portal_ticket_user_status", "user_id", "status"),
        Index("ix_portal_ticket_org_status", "organization_id", "status"),
        Index("ix_portal_ticket_assigned", "assigned_to", "status"),
    )


class PortalAnnouncement(BaseModel):
    """System announcements for portal users.

    Broadcast messages visible to all or specific user segments.
    """

    __tablename__ = "portal_announcement"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    announcement_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # INFO, WARNING, CRITICAL, MAINTENANCE

    # Display
    display_position: Mapped[str] = mapped_column(
        String(50), default="BANNER"
    )  # BANNER, MODAL, INLINE
    action_url: Mapped[Optional[str]] = mapped_column(String(500))
    action_text: Mapped[Optional[str]] = mapped_column(String(100))

    # Targeting
    target_audience: Mapped[str] = mapped_column(
        String(50), default="ALL"
    )  # ALL, SEGMENT, SPECIFIC_USERS
    target_segment: Mapped[Optional[str]] = mapped_column(Text)  # JSON criteria

    # Schedule
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_dismissible: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metrics
    view_count: Mapped[int] = mapped_column(default=0)
    dismiss_count: Mapped[int] = mapped_column(default=0)
    click_count: Mapped[int] = mapped_column(default=0)

    __table_args__ = (
        Index("ix_portal_announcement_active", "organization_id", "is_active"),
    )
