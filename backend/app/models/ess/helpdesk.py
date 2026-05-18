"""Helpdesk Ticket models for ESS Portal."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum as SQLEnum,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.ess.enums import (
    TicketCategory,
    TicketPriority,
    TicketStatus,
)

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.hris.employee import Employee
    from app.models.ess.ess_user import ESSUser
    from app.models.auth.user import User


class TicketCategoryMaster(BaseModel):
    """Master for helpdesk ticket categories with SLA configuration."""

    __tablename__ = "mst_helpdesk_category"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "code", name="uq_helpdesk_category_org_code"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Category Details
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    category_type: Mapped[str] = mapped_column(
        SQLEnum(TicketCategory, name="ticket_category_enum", create_type=False),
        nullable=False,
    )

    # Department (HR / IT)
    department: Mapped[str] = mapped_column(String(20), nullable=False)  # HR, IT

    # SLA Configuration (in hours)
    response_sla_hours: Mapped[int] = mapped_column(Integer, default=4)
    resolution_sla_hours: Mapped[int] = mapped_column(Integer, default=48)

    # Priority-wise SLA overrides (stored as JSON)
    sla_by_priority: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Example: {"HIGH": {"response": 2, "resolution": 24}, "URGENT": {"response": 1, "resolution": 8}}

    # Auto Assignment
    auto_assign: Mapped[bool] = mapped_column(Boolean, default=False)
    default_assignee_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    assignment_queue: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Escalation
    enable_escalation: Mapped[bool] = mapped_column(Boolean, default=True)
    escalation_after_hours: Mapped[int] = mapped_column(Integer, default=24)
    escalate_to_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Notification Template
    notification_template: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    tickets: Mapped[List["HelpdeskTicket"]] = relationship(
        "HelpdeskTicket", back_populates="category", lazy="selectin"
    )


class HelpdeskTicket(BaseModel):
    """Employee helpdesk tickets."""

    __tablename__ = "ess_helpdesk_ticket"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "ticket_number", name="uq_helpdesk_ticket_org_number"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ESS User (Requester)
    ess_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ess_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Employee
    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Ticket Details
    ticket_number: Mapped[str] = mapped_column(String(30), nullable=False)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Category
    category_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_helpdesk_category.id", ondelete="SET NULL"),
        nullable=True,
    )
    category_type: Mapped[str] = mapped_column(
        SQLEnum(TicketCategory, name="ticket_category_enum", create_type=False),
        nullable=False,
    )

    # Priority
    priority: Mapped[str] = mapped_column(
        SQLEnum(TicketPriority, name="ticket_priority_enum", create_type=False),
        default=TicketPriority.NORMAL,
        nullable=False,
    )

    # Attachments
    attachments: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Assignment
    assigned_to: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    assigned_department: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # SLA
    sla_response_hours: Mapped[int] = mapped_column(Integer, default=4)
    sla_resolution_hours: Mapped[int] = mapped_column(Integer, default=48)
    response_due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolution_due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    first_response_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    response_sla_breached: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_sla_breached: Mapped[bool] = mapped_column(Boolean, default=False)

    # Resolution
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Closure
    closed_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closure_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Feedback
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Escalation
    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    escalated_to: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    escalated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    escalation_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Reopen Count
    reopen_count: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(TicketStatus, name="ticket_status_enum", create_type=False),
        default=TicketStatus.OPEN,
        nullable=False,
    )

    # Related Ticket (for follow-up)
    parent_ticket_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ess_helpdesk_ticket.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    ess_user: Mapped["ESSUser"] = relationship(
        "ESSUser", back_populates="helpdesk_tickets", lazy="selectin"
    )
    employee: Mapped["Employee"] = relationship(
        "Employee", lazy="selectin"
    )
    category: Mapped[Optional["TicketCategoryMaster"]] = relationship(
        "TicketCategoryMaster", back_populates="tickets", lazy="selectin"
    )
    comments: Mapped[List["TicketComment"]] = relationship(
        "TicketComment", back_populates="ticket", lazy="selectin", cascade="all, delete-orphan"
    )
    history: Mapped[List["TicketHistory"]] = relationship(
        "TicketHistory", back_populates="ticket", lazy="selectin", cascade="all, delete-orphan"
    )


class TicketComment(BaseModel):
    """Comments/replies on helpdesk tickets."""

    __tablename__ = "ess_ticket_comment"

    # Ticket Reference
    ticket_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ess_helpdesk_ticket.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Author (can be employee or support staff)
    author_type: Mapped[str] = mapped_column(String(20), nullable=False)  # EMPLOYEE, SUPPORT
    ess_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ess_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Comment
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)  # Internal notes not visible to employee

    # Attachments
    attachments: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    ticket: Mapped["HelpdeskTicket"] = relationship(
        "HelpdeskTicket", back_populates="comments", lazy="selectin"
    )


class TicketHistory(BaseModel):
    """Status change history for tickets."""

    __tablename__ = "ess_ticket_history"

    # Ticket Reference
    ticket_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ess_helpdesk_ticket.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Change Details
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # CREATED, ASSIGNED, STATUS_CHANGE, ESCALATED, etc.
    field_changed: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    old_value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Actor
    changed_by_type: Mapped[str] = mapped_column(String(20), nullable=False)  # EMPLOYEE, SUPPORT, SYSTEM
    ess_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ess_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Timestamp
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    ticket: Mapped["HelpdeskTicket"] = relationship(
        "HelpdeskTicket", back_populates="history", lazy="selectin"
    )
