"""ESS Helpdesk Ticket Service."""

from datetime import date, datetime, timedelta
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ess.helpdesk import (
    TicketCategoryMaster,
    HelpdeskTicket,
    TicketComment,
    TicketHistory,
)
from app.models.ess.enums import (
    TicketCategory,
    TicketPriority,
    TicketStatus,
)


class ESSHelpdeskService:
    """Service for ESS Helpdesk Ticket management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== Category Management ====================

    async def get_categories(
        self,
        organization_id: UUID,
        department: Optional[str] = None,
        active_only: bool = True,
    ) -> List[TicketCategoryMaster]:
        """Get helpdesk categories."""
        query = select(TicketCategoryMaster).where(
            TicketCategoryMaster.organization_id == organization_id
        )
        if department:
            query = query.where(TicketCategoryMaster.department == department)
        if active_only:
            query = query.where(TicketCategoryMaster.is_active == True)
        query = query.order_by(TicketCategoryMaster.name)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_category_by_id(
        self, category_id: UUID
    ) -> Optional[TicketCategoryMaster]:
        """Get category by ID."""
        query = select(TicketCategoryMaster).where(
            TicketCategoryMaster.id == category_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    # ==================== Ticket Management ====================

    async def generate_ticket_number(self, organization_id: UUID) -> str:
        """Generate unique ticket number."""
        today = date.today()
        prefix = f"TKT{today.strftime('%Y%m')}"

        # Get count of tickets this month
        query = select(func.count()).select_from(HelpdeskTicket).where(
            and_(
                HelpdeskTicket.organization_id == organization_id,
                HelpdeskTicket.ticket_number.like(f"{prefix}%")
            )
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0

        return f"{prefix}{count + 1:04d}"

    async def create_ticket(
        self,
        organization_id: UUID,
        ess_user_id: UUID,
        employee_id: UUID,
        subject: str,
        description: str,
        category_type: TicketCategory,
        priority: TicketPriority = TicketPriority.NORMAL,
        category_id: Optional[UUID] = None,
        attachments: Optional[dict] = None,
    ) -> HelpdeskTicket:
        """Create a new helpdesk ticket."""
        ticket_number = await self.generate_ticket_number(organization_id)

        # Get SLA from category if available
        sla_response = 4
        sla_resolution = 48
        department = "HR"

        if category_id:
            category = await self.get_category_by_id(category_id)
            if category:
                sla_response = category.response_sla_hours
                sla_resolution = category.resolution_sla_hours
                department = category.department

                # Apply priority-wise SLA if defined
                if category.sla_by_priority and priority.value in category.sla_by_priority:
                    priority_sla = category.sla_by_priority[priority.value]
                    sla_response = priority_sla.get("response", sla_response)
                    sla_resolution = priority_sla.get("resolution", sla_resolution)

        # Calculate due dates
        now = datetime.utcnow()
        response_due = now + timedelta(hours=sla_response)
        resolution_due = now + timedelta(hours=sla_resolution)

        ticket = HelpdeskTicket(
            organization_id=organization_id,
            ess_user_id=ess_user_id,
            employee_id=employee_id,
            ticket_number=ticket_number,
            subject=subject,
            description=description,
            category_id=category_id,
            category_type=category_type,
            priority=priority,
            attachments=attachments,
            assigned_department=department,
            sla_response_hours=sla_response,
            sla_resolution_hours=sla_resolution,
            response_due_at=response_due,
            resolution_due_at=resolution_due,
            status=TicketStatus.OPEN,
        )
        self.session.add(ticket)
        await self.session.flush()

        # Record creation in history
        await self._add_history(
            ticket_id=ticket.id,
            action="CREATED",
            new_value=TicketStatus.OPEN.value,
            changed_by_type="EMPLOYEE",
            ess_user_id=ess_user_id,
        )

        # Auto-assign if category has default assignee
        if category_id:
            category = await self.get_category_by_id(category_id)
            if category and category.auto_assign and category.default_assignee_id:
                await self.assign_ticket(
                    ticket_id=ticket.id,
                    assignee_id=category.default_assignee_id,
                    assigned_by_type="SYSTEM",
                )

        return ticket

    async def get_ticket_by_id(
        self,
        ticket_id: UUID,
        include_comments: bool = True,
        include_history: bool = False,
    ) -> Optional[HelpdeskTicket]:
        """Get ticket by ID."""
        query = select(HelpdeskTicket).where(
            HelpdeskTicket.id == ticket_id
        )
        if include_comments:
            query = query.options(selectinload(HelpdeskTicket.comments))
        if include_history:
            query = query.options(selectinload(HelpdeskTicket.history))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_ticket_by_number(
        self,
        ticket_number: str,
    ) -> Optional[HelpdeskTicket]:
        """Get ticket by ticket number."""
        query = select(HelpdeskTicket).where(
            HelpdeskTicket.ticket_number == ticket_number
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_tickets_by_employee(
        self,
        employee_id: UUID,
        status: Optional[TicketStatus] = None,
        category_type: Optional[TicketCategory] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[HelpdeskTicket], int]:
        """Get tickets for an employee with filters."""
        query = select(HelpdeskTicket).where(
            HelpdeskTicket.employee_id == employee_id
        )

        if status:
            query = query.where(HelpdeskTicket.status == status)
        if category_type:
            query = query.where(HelpdeskTicket.category_type == category_type)
        if from_date:
            query = query.where(func.date(HelpdeskTicket.created_at) >= from_date)
        if to_date:
            query = query.where(func.date(HelpdeskTicket.created_at) <= to_date)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.order_by(HelpdeskTicket.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_tickets_for_support(
        self,
        organization_id: UUID,
        assignee_id: Optional[UUID] = None,
        department: Optional[str] = None,
        status: Optional[List[TicketStatus]] = None,
        priority: Optional[TicketPriority] = None,
        sla_breached: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[HelpdeskTicket], int]:
        """Get tickets for support staff."""
        query = select(HelpdeskTicket).where(
            HelpdeskTicket.organization_id == organization_id
        )

        if assignee_id:
            query = query.where(HelpdeskTicket.assigned_to == assignee_id)
        if department:
            query = query.where(HelpdeskTicket.assigned_department == department)
        if status:
            query = query.where(HelpdeskTicket.status.in_(status))
        if priority:
            query = query.where(HelpdeskTicket.priority == priority)
        if sla_breached is not None:
            query = query.where(
                or_(
                    HelpdeskTicket.response_sla_breached == sla_breached,
                    HelpdeskTicket.resolution_sla_breached == sla_breached,
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination - urgent/high priority first, then by creation date
        query = query.order_by(
            HelpdeskTicket.priority.desc(),
            HelpdeskTicket.created_at.asc()
        )
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    # ==================== Ticket Actions ====================

    async def assign_ticket(
        self,
        ticket_id: UUID,
        assignee_id: UUID,
        assigned_by_type: str = "SUPPORT",
        user_id: Optional[UUID] = None,
        remarks: Optional[str] = None,
    ) -> Optional[HelpdeskTicket]:
        """Assign ticket to support staff."""
        ticket = await self.get_ticket_by_id(ticket_id, include_comments=False)
        if not ticket:
            return None

        old_assignee = str(ticket.assigned_to) if ticket.assigned_to else None
        ticket.assigned_to = assignee_id
        ticket.assigned_date = datetime.utcnow()
        ticket.status = TicketStatus.ASSIGNED

        await self._add_history(
            ticket_id=ticket_id,
            action="ASSIGNED",
            field_changed="assigned_to",
            old_value=old_assignee,
            new_value=str(assignee_id),
            remarks=remarks,
            changed_by_type=assigned_by_type,
            user_id=user_id,
        )

        await self.session.flush()
        return ticket

    async def update_status(
        self,
        ticket_id: UUID,
        new_status: TicketStatus,
        user_id: UUID,
        remarks: Optional[str] = None,
    ) -> Optional[HelpdeskTicket]:
        """Update ticket status."""
        ticket = await self.get_ticket_by_id(ticket_id, include_comments=False)
        if not ticket:
            return None

        old_status = ticket.status.value
        ticket.status = new_status

        # Record first response if moving from OPEN/ASSIGNED
        if new_status == TicketStatus.IN_PROGRESS and not ticket.first_response_at:
            ticket.first_response_at = datetime.utcnow()
            # Check SLA breach
            if ticket.response_due_at and datetime.utcnow() > ticket.response_due_at:
                ticket.response_sla_breached = True

        await self._add_history(
            ticket_id=ticket_id,
            action="STATUS_CHANGE",
            field_changed="status",
            old_value=old_status,
            new_value=new_status.value,
            remarks=remarks,
            changed_by_type="SUPPORT",
            user_id=user_id,
        )

        await self.session.flush()
        return ticket

    async def resolve_ticket(
        self,
        ticket_id: UUID,
        resolution: str,
        resolved_by: UUID,
    ) -> Optional[HelpdeskTicket]:
        """Resolve a ticket."""
        ticket = await self.get_ticket_by_id(ticket_id, include_comments=False)
        if not ticket:
            return None

        ticket.status = TicketStatus.RESOLVED
        ticket.resolution = resolution
        ticket.resolution_date = datetime.utcnow()
        ticket.resolved_by = resolved_by

        # Check SLA breach
        if ticket.resolution_due_at and datetime.utcnow() > ticket.resolution_due_at:
            ticket.resolution_sla_breached = True

        await self._add_history(
            ticket_id=ticket_id,
            action="RESOLVED",
            new_value=TicketStatus.RESOLVED.value,
            remarks=resolution,
            changed_by_type="SUPPORT",
            user_id=resolved_by,
        )

        await self.session.flush()
        return ticket

    async def close_ticket(
        self,
        ticket_id: UUID,
        closed_by_type: str = "EMPLOYEE",
        ess_user_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        remarks: Optional[str] = None,
    ) -> Optional[HelpdeskTicket]:
        """Close a resolved ticket."""
        ticket = await self.get_ticket_by_id(ticket_id, include_comments=False)
        if not ticket:
            return None

        if ticket.status != TicketStatus.RESOLVED:
            raise ValueError("Only resolved tickets can be closed")

        ticket.status = TicketStatus.CLOSED
        ticket.closed_date = datetime.utcnow()
        ticket.closure_remarks = remarks

        await self._add_history(
            ticket_id=ticket_id,
            action="CLOSED",
            new_value=TicketStatus.CLOSED.value,
            remarks=remarks,
            changed_by_type=closed_by_type,
            ess_user_id=ess_user_id,
            user_id=user_id,
        )

        await self.session.flush()
        return ticket

    async def reopen_ticket(
        self,
        ticket_id: UUID,
        reason: str,
        ess_user_id: UUID,
    ) -> Optional[HelpdeskTicket]:
        """Reopen a closed/resolved ticket."""
        ticket = await self.get_ticket_by_id(ticket_id, include_comments=False)
        if not ticket:
            return None

        if ticket.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            raise ValueError("Only resolved/closed tickets can be reopened")

        ticket.status = TicketStatus.REOPENED
        ticket.reopen_count += 1

        await self._add_history(
            ticket_id=ticket_id,
            action="REOPENED",
            new_value=TicketStatus.REOPENED.value,
            remarks=reason,
            changed_by_type="EMPLOYEE",
            ess_user_id=ess_user_id,
        )

        await self.session.flush()
        return ticket

    async def escalate_ticket(
        self,
        ticket_id: UUID,
        escalate_to: UUID,
        reason: str,
        escalated_by_type: str = "SYSTEM",
        user_id: Optional[UUID] = None,
    ) -> Optional[HelpdeskTicket]:
        """Escalate a ticket."""
        ticket = await self.get_ticket_by_id(ticket_id, include_comments=False)
        if not ticket:
            return None

        ticket.is_escalated = True
        ticket.escalated_to = escalate_to
        ticket.escalated_at = datetime.utcnow()
        ticket.escalation_reason = reason

        await self._add_history(
            ticket_id=ticket_id,
            action="ESCALATED",
            field_changed="escalated_to",
            new_value=str(escalate_to),
            remarks=reason,
            changed_by_type=escalated_by_type,
            user_id=user_id,
        )

        await self.session.flush()
        return ticket

    # ==================== Comments ====================

    async def add_comment(
        self,
        ticket_id: UUID,
        comment: str,
        author_type: str,
        ess_user_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        is_internal: bool = False,
        attachments: Optional[dict] = None,
    ) -> TicketComment:
        """Add a comment to a ticket."""
        ticket = await self.get_ticket_by_id(ticket_id, include_comments=False)
        if not ticket:
            raise ValueError("Ticket not found")

        if ticket.status in [TicketStatus.CLOSED, TicketStatus.CANCELLED]:
            raise ValueError("Cannot comment on closed ticket")

        ticket_comment = TicketComment(
            ticket_id=ticket_id,
            author_type=author_type,
            ess_user_id=ess_user_id,
            user_id=user_id,
            comment=comment,
            is_internal=is_internal,
            attachments=attachments,
        )
        self.session.add(ticket_comment)

        # Record first response if from support and not yet recorded
        if author_type == "SUPPORT" and not ticket.first_response_at:
            ticket.first_response_at = datetime.utcnow()
            if ticket.response_due_at and datetime.utcnow() > ticket.response_due_at:
                ticket.response_sla_breached = True

        await self.session.flush()
        return ticket_comment

    async def get_comments(
        self,
        ticket_id: UUID,
        include_internal: bool = False,
    ) -> List[TicketComment]:
        """Get comments for a ticket."""
        query = select(TicketComment).where(
            TicketComment.ticket_id == ticket_id
        )
        if not include_internal:
            query = query.where(TicketComment.is_internal == False)
        query = query.order_by(TicketComment.created_at.asc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ==================== Feedback ====================

    async def submit_feedback(
        self,
        ticket_id: UUID,
        rating: int,
        feedback: Optional[str] = None,
    ) -> Optional[HelpdeskTicket]:
        """Submit feedback for a resolved ticket."""
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        ticket = await self.get_ticket_by_id(ticket_id, include_comments=False)
        if not ticket:
            return None

        if ticket.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            raise ValueError("Feedback can only be submitted for resolved tickets")

        ticket.rating = rating
        ticket.feedback = feedback
        ticket.feedback_date = datetime.utcnow()

        await self.session.flush()
        return ticket

    # ==================== Internal Helpers ====================

    async def _add_history(
        self,
        ticket_id: UUID,
        action: str,
        field_changed: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        remarks: Optional[str] = None,
        changed_by_type: str = "SYSTEM",
        ess_user_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> TicketHistory:
        """Add history entry for a ticket."""
        history = TicketHistory(
            ticket_id=ticket_id,
            action=action,
            field_changed=field_changed,
            old_value=old_value,
            new_value=new_value,
            remarks=remarks,
            changed_by_type=changed_by_type,
            ess_user_id=ess_user_id,
            user_id=user_id,
            changed_at=datetime.utcnow(),
        )
        self.session.add(history)
        return history

    # ==================== SLA Monitoring ====================

    async def check_sla_breaches(
        self,
        organization_id: UUID,
    ) -> List[HelpdeskTicket]:
        """Check and update SLA breaches."""
        now = datetime.utcnow()

        # Find tickets with potential SLA breach
        query = select(HelpdeskTicket).where(
            and_(
                HelpdeskTicket.organization_id == organization_id,
                HelpdeskTicket.status.in_([
                    TicketStatus.OPEN,
                    TicketStatus.ASSIGNED,
                    TicketStatus.IN_PROGRESS,
                    TicketStatus.PENDING_INFO,
                ]),
                or_(
                    and_(
                        HelpdeskTicket.response_sla_breached == False,
                        HelpdeskTicket.first_response_at.is_(None),
                        HelpdeskTicket.response_due_at < now,
                    ),
                    and_(
                        HelpdeskTicket.resolution_sla_breached == False,
                        HelpdeskTicket.resolution_date.is_(None),
                        HelpdeskTicket.resolution_due_at < now,
                    ),
                )
            )
        )

        result = await self.session.execute(query)
        tickets = list(result.scalars().all())

        breached_tickets = []
        for ticket in tickets:
            updated = False
            if not ticket.first_response_at and ticket.response_due_at and now > ticket.response_due_at:
                ticket.response_sla_breached = True
                updated = True
            if not ticket.resolution_date and ticket.resolution_due_at and now > ticket.resolution_due_at:
                ticket.resolution_sla_breached = True
                updated = True

            if updated:
                breached_tickets.append(ticket)

        await self.session.flush()
        return breached_tickets

    # ==================== Analytics ====================

    async def get_ticket_summary(
        self,
        employee_id: UUID,
    ) -> dict:
        """Get ticket summary for an employee."""
        query = select(
            HelpdeskTicket.status,
            func.count().label("count"),
        ).where(
            HelpdeskTicket.employee_id == employee_id
        ).group_by(HelpdeskTicket.status)

        result = await self.session.execute(query)
        rows = result.all()

        summary = {
            "total": 0,
            "open": 0,
            "in_progress": 0,
            "resolved": 0,
            "closed": 0,
            "by_status": {}
        }

        for row in rows:
            status = row.status.value if row.status else "UNKNOWN"
            summary["by_status"][status] = row.count
            summary["total"] += row.count

            if row.status in [TicketStatus.OPEN, TicketStatus.ASSIGNED]:
                summary["open"] += row.count
            elif row.status == TicketStatus.IN_PROGRESS:
                summary["in_progress"] += row.count
            elif row.status == TicketStatus.RESOLVED:
                summary["resolved"] += row.count
            elif row.status == TicketStatus.CLOSED:
                summary["closed"] += row.count

        return summary
