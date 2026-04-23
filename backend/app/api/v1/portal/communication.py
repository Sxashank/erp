"""Portal Communication API endpoints."""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.v1.portal.auth import get_portal_user
from app.models.portal.enums import (
    TicketCategory,
    TicketPriority,
    TicketStatus,
)
from app.services.portal.notification_service import PortalNotificationService

router = APIRouter(prefix="/communication", tags=["Portal Communication"])


# =============================================================================
# Request/Response Schemas
# =============================================================================


class NotificationResponse(BaseModel):
    """Notification response."""

    id: str
    title: str
    body: str
    notification_type: str
    channel: str
    priority: str
    action_url: Optional[str] = None
    is_read: bool
    created_at: str


class MessageSendRequest(BaseModel):
    """Send message request."""

    subject: Optional[str] = None
    body: str = Field(..., min_length=1)
    thread_id: Optional[UUID] = None
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None


class MessageResponse(BaseModel):
    """Message response."""

    id: str
    thread_id: Optional[str] = None
    subject: Optional[str] = None
    body: str
    is_from_customer: bool
    sender_name: Optional[str] = None
    is_read: bool
    has_attachments: bool
    created_at: str


class TicketCreateRequest(BaseModel):
    """Create ticket request."""

    subject: str = Field(..., max_length=255)
    description: str
    category: TicketCategory
    priority: TicketPriority = TicketPriority.MEDIUM
    sub_category: Optional[str] = None
    loan_account_id: Optional[UUID] = None


class TicketResponse(BaseModel):
    """Ticket response."""

    id: str
    ticket_number: str
    subject: str
    category: str
    priority: str
    status: str
    created_at: str
    sla_due_at: Optional[str] = None
    is_sla_breached: bool


class TicketDetails(BaseModel):
    """Detailed ticket response."""

    id: str
    ticket_number: str
    subject: str
    description: str
    category: str
    sub_category: Optional[str] = None
    priority: str
    status: str
    created_at: str
    sla_due_at: Optional[str] = None
    is_sla_breached: bool
    resolved_at: Optional[str] = None
    resolution_summary: Optional[str] = None
    customer_rating: Optional[int] = None
    customer_feedback: Optional[str] = None
    messages: List[dict]


class TicketReplyRequest(BaseModel):
    """Reply to ticket request."""

    message: str = Field(..., min_length=1)


class TicketRatingRequest(BaseModel):
    """Rate ticket request."""

    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


class AnnouncementResponse(BaseModel):
    """Announcement response."""

    id: str
    title: str
    body: str
    announcement_type: str
    display_position: str
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    is_dismissible: bool


class PaginatedResponse(BaseModel):
    """Paginated response."""

    items: List
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Notifications
# =============================================================================


@router.get(
    "/notifications",
    response_model=PaginatedResponse,
    summary="Get Notifications",
)
async def get_notifications(
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Get notifications for the user."""
    service = PortalNotificationService(db)
    items, total = await service.get_notifications(
        user_id=user.id,
        is_read=is_read,
        notification_type=notification_type,
        page=page,
        page_size=page_size,
    )

    return PaginatedResponse(
        items=[NotificationResponse(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.get(
    "/notifications/unread-count",
    summary="Get Unread Count",
)
async def get_unread_count(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Get count of unread notifications."""
    service = PortalNotificationService(db)
    count = await service.get_unread_count(user.id)

    return {"unread_count": count}


@router.post(
    "/notifications/{notification_id}/read",
    summary="Mark as Read",
)
async def mark_notification_read(
    notification_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    service = PortalNotificationService(db)
    success = await service.mark_as_read(notification_id, user.id)
    await db.commit()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return {"message": "Marked as read"}


@router.post(
    "/notifications/read-all",
    summary="Mark All as Read",
)
async def mark_all_notifications_read(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read."""
    service = PortalNotificationService(db)
    count = await service.mark_all_as_read(user.id)
    await db.commit()

    return {"message": f"Marked {count} notifications as read"}


# =============================================================================
# Messages
# =============================================================================


@router.post(
    "/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send Message",
)
async def send_message(
    request: MessageSendRequest,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to support."""
    service = PortalNotificationService(db)
    message = await service.send_message(
        organization_id=user.organization_id,
        user_id=user.id,
        **request.model_dump(),
    )
    await db.commit()

    return MessageResponse(
        id=str(message.id),
        thread_id=str(message.thread_id) if message.thread_id else None,
        subject=message.subject,
        body=message.body,
        is_from_customer=message.is_from_customer,
        sender_name=message.sender_name,
        is_read=message.is_read,
        has_attachments=message.has_attachments,
        created_at=message.created_at.isoformat(),
    )


@router.get(
    "/messages",
    response_model=PaginatedResponse,
    summary="Get Messages",
)
async def get_messages(
    thread_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Get messages."""
    service = PortalNotificationService(db)
    items, total = await service.get_messages(
        user_id=user.id,
        thread_id=thread_id,
        page=page,
        page_size=page_size,
    )

    return PaginatedResponse(
        items=[MessageResponse(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.post(
    "/messages/{message_id}/read",
    summary="Mark Message as Read",
)
async def mark_message_read(
    message_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a message as read."""
    service = PortalNotificationService(db)
    success = await service.mark_message_read(message_id, user.id)
    await db.commit()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    return {"message": "Marked as read"}


# =============================================================================
# Support Tickets
# =============================================================================


@router.post(
    "/tickets",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Support Ticket",
)
async def create_ticket(
    request: TicketCreateRequest,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new support ticket."""
    service = PortalNotificationService(db)
    ticket = await service.create_ticket(
        organization_id=user.organization_id,
        user_id=user.id,
        **request.model_dump(),
    )
    await db.commit()

    return TicketResponse(
        id=str(ticket.id),
        ticket_number=ticket.ticket_number,
        subject=ticket.subject,
        category=ticket.category.value,
        priority=ticket.priority.value,
        status=ticket.status.value,
        created_at=ticket.created_at.isoformat(),
        sla_due_at=ticket.sla_due_at.isoformat() if ticket.sla_due_at else None,
        is_sla_breached=ticket.is_sla_breached,
    )


@router.get(
    "/tickets",
    response_model=PaginatedResponse,
    summary="Get Tickets",
)
async def get_tickets(
    status: Optional[TicketStatus] = None,
    category: Optional[TicketCategory] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Get support tickets."""
    service = PortalNotificationService(db)
    items, total = await service.get_tickets(
        user_id=user.id,
        status=status,
        category=category,
        page=page,
        page_size=page_size,
    )

    return PaginatedResponse(
        items=[TicketResponse(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketDetails,
    summary="Get Ticket Details",
)
async def get_ticket_details(
    ticket_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Get ticket details with message history."""
    service = PortalNotificationService(db)
    details = await service.get_ticket_details(ticket_id, user.id)

    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    return TicketDetails(**details)


@router.post(
    "/tickets/{ticket_id}/reply",
    response_model=MessageResponse,
    summary="Reply to Ticket",
)
async def reply_to_ticket(
    ticket_id: UUID,
    request: TicketReplyRequest,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a reply to a ticket."""
    service = PortalNotificationService(db)

    try:
        message = await service.add_ticket_reply(
            ticket_id=ticket_id,
            user_id=user.id,
            message=request.message,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    return MessageResponse(
        id=str(message.id),
        thread_id=None,
        subject=None,
        body=message.body,
        is_from_customer=message.is_from_customer,
        sender_name=message.sender_name,
        is_read=message.is_read,
        has_attachments=message.has_attachments,
        created_at=message.created_at.isoformat(),
    )


@router.post(
    "/tickets/{ticket_id}/rate",
    summary="Rate Ticket",
)
async def rate_ticket(
    ticket_id: UUID,
    request: TicketRatingRequest,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Rate a resolved/closed ticket."""
    service = PortalNotificationService(db)

    try:
        success = await service.rate_ticket(
            ticket_id=ticket_id,
            user_id=user.id,
            rating=request.rating,
            feedback=request.feedback,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found or not resolved",
        )

    return {"message": "Rating submitted"}


# =============================================================================
# Announcements
# =============================================================================


@router.get(
    "/announcements",
    response_model=List[AnnouncementResponse],
    summary="Get Announcements",
)
async def get_announcements(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Get active announcements."""
    service = PortalNotificationService(db)
    announcements = await service.get_active_announcements(
        organization_id=user.organization_id,
    )

    return [AnnouncementResponse(**a) for a in announcements]


@router.post(
    "/announcements/{announcement_id}/view",
    summary="Record Announcement View",
)
async def record_announcement_view(
    announcement_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Record that user viewed an announcement."""
    service = PortalNotificationService(db)
    await service.record_announcement_view(announcement_id)
    await db.commit()

    return {"message": "View recorded"}


@router.post(
    "/announcements/{announcement_id}/dismiss",
    summary="Dismiss Announcement",
)
async def dismiss_announcement(
    announcement_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss an announcement."""
    service = PortalNotificationService(db)
    await service.record_announcement_dismiss(announcement_id)
    await db.commit()

    return {"message": "Announcement dismissed"}


@router.post(
    "/announcements/{announcement_id}/click",
    summary="Record Announcement Click",
)
async def record_announcement_click(
    announcement_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Record that user clicked announcement action."""
    service = PortalNotificationService(db)
    await service.record_announcement_click(announcement_id)
    await db.commit()

    return {"message": "Click recorded"}
