"""ESS Helpdesk Ticket API endpoints."""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.services.ess.helpdesk_service import ESSHelpdeskService
from app.models.ess.enums import TicketCategory, TicketPriority, TicketStatus
from app.core.exceptions import BadRequestException, NotFoundException


router = APIRouter(prefix="/helpdesk", tags=["ESS Helpdesk"])


# ==================== Schemas ====================

class TicketCategoryResponse(BaseModel):
    """Ticket category response."""
    id: str
    code: str
    name: str
    description: Optional[str]
    department: str
    response_sla_hours: int
    resolution_sla_hours: int


class TicketCreate(BaseModel):
    """Create helpdesk ticket."""
    subject: str = Field(..., max_length=300)
    description: str
    category_type: TicketCategory
    category_id: Optional[UUID] = None
    priority: TicketPriority = TicketPriority.NORMAL
    attachments: Optional[dict] = None


class CommentCreate(BaseModel):
    """Add comment to ticket."""
    comment: str


class FeedbackCreate(BaseModel):
    """Submit feedback for ticket."""
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


class TicketCommentResponse(BaseModel):
    """Ticket comment response."""
    id: str
    author_type: str
    comment: str
    attachments: Optional[dict]
    created_at: str


class TicketResponse(BaseModel):
    """Ticket response."""
    id: str
    ticket_number: str
    subject: str
    category_type: str
    priority: str
    status: str
    assigned_department: Optional[str]
    created_at: str
    response_sla_breached: bool
    resolution_sla_breached: bool


class TicketDetailResponse(TicketResponse):
    """Detailed ticket response."""
    description: str
    category: Optional[str]
    assigned_to: Optional[str]
    assigned_date: Optional[str]
    resolution: Optional[str]
    resolution_date: Optional[str]
    closed_date: Optional[str]
    rating: Optional[int]
    feedback: Optional[str]
    response_due_at: Optional[str]
    resolution_due_at: Optional[str]
    first_response_at: Optional[str]
    is_escalated: bool
    reopen_count: int
    comments: List[TicketCommentResponse]


class TicketSummaryResponse(BaseModel):
    """Ticket summary response."""
    total: int
    open: int
    in_progress: int
    resolved: int
    closed: int
    by_status: dict


# ==================== Endpoints ====================

@router.get("/categories", response_model=List[TicketCategoryResponse], response_model_by_alias=True)
async def get_categories(
    organization_id: UUID,  # From authenticated user
    department: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """Get helpdesk categories."""
    service = ESSHelpdeskService(session)
    categories = await service.get_categories(
        organization_id=organization_id,
        department=department,
    )

    return [
        TicketCategoryResponse(
            id=str(c.id),
            code=c.code,
            name=c.name,
            description=c.description,
            department=c.department,
            response_sla_hours=c.response_sla_hours,
            resolution_sla_hours=c.resolution_sla_hours,
        )
        for c in categories
    ]


@router.post("", response_model=TicketResponse, response_model_by_alias=True)
async def create_ticket(
    request: TicketCreate,
    organization_id: UUID,  # From authenticated user
    ess_user_id: UUID,  # From authenticated user
    employee_id: UUID,  # From authenticated user
    session: AsyncSession = Depends(get_session),
):
    """Create a new helpdesk ticket."""
    service = ESSHelpdeskService(session)

    ticket = await service.create_ticket(
        organization_id=organization_id,
        ess_user_id=ess_user_id,
        employee_id=employee_id,
        subject=request.subject,
        description=request.description,
        category_type=request.category_type,
        category_id=request.category_id,
        priority=request.priority,
        attachments=request.attachments,
    )

    await session.commit()

    return TicketResponse(
        id=str(ticket.id),
        ticket_number=ticket.ticket_number,
        subject=ticket.subject,
        category_type=ticket.category_type.value,
        priority=ticket.priority.value,
        status=ticket.status.value,
        assigned_department=ticket.assigned_department,
        created_at=ticket.created_at.isoformat(),
        response_sla_breached=ticket.response_sla_breached,
        resolution_sla_breached=ticket.resolution_sla_breached,
    )


@router.get("", response_model=List[TicketResponse], response_model_by_alias=True)
async def get_tickets(
    employee_id: UUID,  # From authenticated user
    status: Optional[TicketStatus] = None,
    category_type: Optional[TicketCategory] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Get tickets for the employee."""
    service = ESSHelpdeskService(session)

    tickets, total = await service.get_tickets_by_employee(
        employee_id=employee_id,
        status=status,
        category_type=category_type,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )

    return [
        TicketResponse(
            id=str(t.id),
            ticket_number=t.ticket_number,
            subject=t.subject,
            category_type=t.category_type.value,
            priority=t.priority.value,
            status=t.status.value,
            assigned_department=t.assigned_department,
            created_at=t.created_at.isoformat(),
            response_sla_breached=t.response_sla_breached,
            resolution_sla_breached=t.resolution_sla_breached,
        )
        for t in tickets
    ]


@router.get("/summary", response_model=TicketSummaryResponse, response_model_by_alias=True)
async def get_ticket_summary(
    employee_id: UUID,  # From authenticated user
    session: AsyncSession = Depends(get_session),
):
    """Get ticket summary for the employee."""
    service = ESSHelpdeskService(session)
    summary = await service.get_ticket_summary(employee_id)
    return TicketSummaryResponse(**summary)


@router.get("/{ticket_id}", response_model=TicketDetailResponse, response_model_by_alias=True)
async def get_ticket_detail(
    ticket_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get ticket details with comments."""
    service = ESSHelpdeskService(session)
    ticket = await service.get_ticket_by_id(ticket_id, include_comments=True)

    if not ticket:
        raise NotFoundException(detail="Ticket not found", error_code="TICKET_NOT_FOUND")

    return TicketDetailResponse(
        id=str(ticket.id),
        ticket_number=ticket.ticket_number,
        subject=ticket.subject,
        description=ticket.description,
        category_type=ticket.category_type.value,
        category=ticket.category.name if ticket.category else None,
        priority=ticket.priority.value,
        status=ticket.status.value,
        assigned_department=ticket.assigned_department,
        assigned_to=str(ticket.assigned_to) if ticket.assigned_to else None,
        assigned_date=ticket.assigned_date.isoformat() if ticket.assigned_date else None,
        resolution=ticket.resolution,
        resolution_date=ticket.resolution_date.isoformat() if ticket.resolution_date else None,
        closed_date=ticket.closed_date.isoformat() if ticket.closed_date else None,
        rating=ticket.rating,
        feedback=ticket.feedback,
        response_due_at=ticket.response_due_at.isoformat() if ticket.response_due_at else None,
        resolution_due_at=ticket.resolution_due_at.isoformat() if ticket.resolution_due_at else None,
        first_response_at=ticket.first_response_at.isoformat() if ticket.first_response_at else None,
        is_escalated=ticket.is_escalated,
        reopen_count=ticket.reopen_count,
        created_at=ticket.created_at.isoformat(),
        response_sla_breached=ticket.response_sla_breached,
        resolution_sla_breached=ticket.resolution_sla_breached,
        comments=[
            TicketCommentResponse(
                id=str(c.id),
                author_type=c.author_type,
                comment=c.comment,
                attachments=c.attachments,
                created_at=c.created_at.isoformat(),
            )
            for c in ticket.comments
            if not c.is_internal  # Hide internal comments from employee
        ],
    )


@router.post("/{ticket_id}/comments", response_model=TicketCommentResponse, response_model_by_alias=True)
async def add_comment(
    ticket_id: UUID,
    request: CommentCreate,
    ess_user_id: UUID,  # From authenticated user
    session: AsyncSession = Depends(get_session),
):
    """Add a comment to a ticket."""
    service = ESSHelpdeskService(session)

    try:
        comment = await service.add_comment(
            ticket_id=ticket_id,
            comment=request.comment,
            author_type="EMPLOYEE",
            ess_user_id=ess_user_id,
        )
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    await session.commit()

    return TicketCommentResponse(
        id=str(comment.id),
        author_type=comment.author_type,
        comment=comment.comment,
        attachments=comment.attachments,
        created_at=comment.created_at.isoformat(),
    )


@router.post("/{ticket_id}/close")
async def close_ticket(
    ticket_id: UUID,
    remarks: Optional[str] = None,
    ess_user_id: UUID = None,  # From authenticated user
    session: AsyncSession = Depends(get_session),
):
    """Close a resolved ticket."""
    service = ESSHelpdeskService(session)

    try:
        ticket = await service.close_ticket(
            ticket_id=ticket_id,
            closed_by_type="EMPLOYEE",
            ess_user_id=ess_user_id,
            remarks=remarks,
        )
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    if not ticket:
        raise NotFoundException(detail="Ticket not found", error_code="TICKET_NOT_FOUND")

    await session.commit()

    return {"success": True, "message": "Ticket closed successfully"}


@router.post("/{ticket_id}/reopen")
async def reopen_ticket(
    ticket_id: UUID,
    reason: str,
    ess_user_id: UUID,  # From authenticated user
    session: AsyncSession = Depends(get_session),
):
    """Reopen a closed/resolved ticket."""
    service = ESSHelpdeskService(session)

    try:
        ticket = await service.reopen_ticket(
            ticket_id=ticket_id,
            reason=reason,
            ess_user_id=ess_user_id,
        )
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    if not ticket:
        raise NotFoundException(detail="Ticket not found", error_code="TICKET_NOT_FOUND")

    await session.commit()

    return {"success": True, "message": "Ticket reopened successfully"}


@router.post("/{ticket_id}/feedback")
async def submit_feedback(
    ticket_id: UUID,
    request: FeedbackCreate,
    session: AsyncSession = Depends(get_session),
):
    """Submit feedback for a resolved ticket."""
    service = ESSHelpdeskService(session)

    try:
        ticket = await service.submit_feedback(
            ticket_id=ticket_id,
            rating=request.rating,
            feedback=request.feedback,
        )
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    if not ticket:
        raise NotFoundException(detail="Ticket not found", error_code="TICKET_NOT_FOUND")

    await session.commit()

    return {"success": True, "message": "Feedback submitted successfully"}
