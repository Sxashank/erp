"""Notification API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, get_db_with_tenant
from app.models.auth.user import User
from app.models.notification import NotificationCategory
from app.models.notification import NotificationChannel, NotificationStatus
from app.services.notification import NotificationService
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate,
    NotificationPreferenceResponse,
    NotificationLogListResponse,
    NotificationLogWithTitleResponse,
    NotificationStatsResponse,
    MarkReadRequest,
    SendNotificationRequest,
    BulkNotificationRequest,
)
from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException

router = APIRouter()


@router.get("/", response_model=NotificationListResponse, response_model_by_alias=True)
async def list_notifications(
    category: Optional[NotificationCategory] = None,
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get user's notifications with pagination."""
    service = NotificationService(db)
    skip = (page - 1) * page_size

    notifications, total = await service.get_user_notifications(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        category=category,
        unread_only=unread_only,
        skip=skip,
        limit=page_size,
    )

    unread_count = await service.get_unread_count(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
    )

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        page=page,
        page_size=page_size,
        unread_count=unread_count,
    )


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get count of unread notifications."""
    service = NotificationService(db)
    count = await service.get_unread_count(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
    )
    return {"unread_count": count}


@router.get("/logs", response_model=NotificationLogListResponse, response_model_by_alias=True)
async def get_notification_logs(
    notification_id: Optional[UUID] = None,
    channel: Optional[NotificationChannel] = None,
    status_filter: Optional[NotificationStatus] = Query(default=None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get delivery logs for the current tenant's notifications."""
    service = NotificationService(db)
    skip = (page - 1) * page_size
    logs, total = await service.get_delivery_logs(
        organization_id=current_user.organization_id,
        notification_id=notification_id,
        channel=channel,
        status=status_filter,
        skip=skip,
        limit=page_size,
    )
    return NotificationLogListResponse(
        items=[
            NotificationLogWithTitleResponse(
                id=log.id,
                notification_id=log.notification_id,
                notification_title=title,
                channel=log.channel,
                status=log.status,
                attempt_number=log.attempt_number,
                attempted_at=log.attempted_at,
                response_code=log.response_code,
                response_message=log.response_message,
                provider=log.provider,
                provider_message_id=log.provider_message_id,
                cost=log.cost,
                currency=log.currency,
            )
            for log, title in logs
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/preferences",
    response_model=list[NotificationPreferenceResponse],
    response_model_by_alias=True,
)
async def get_preferences(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get user's notification preferences."""
    service = NotificationService(db)
    preferences = await service.get_user_preferences(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
    )
    return [NotificationPreferenceResponse.model_validate(p) for p in preferences]


@router.post(
    "/preferences", response_model=NotificationPreferenceResponse, response_model_by_alias=True
)
async def create_preference(
    data: NotificationPreferenceCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create or update notification preference for a category."""
    service = NotificationService(db)
    preference = await service.update_user_preference(
        user_id=current_user.id,
        category=data.category,
        organization_id=data.organization_id or current_user.organization_id,
        email_enabled=data.email_enabled,
        sms_enabled=data.sms_enabled,
        push_enabled=data.push_enabled,
        in_app_enabled=data.in_app_enabled,
        whatsapp_enabled=data.whatsapp_enabled,
        digest_mode=data.digest_mode,
        digest_frequency=data.digest_frequency,
        quiet_hours_start=data.quiet_hours_start,
        quiet_hours_end=data.quiet_hours_end,
    )
    return NotificationPreferenceResponse.model_validate(preference)


@router.get("/{notification_id}", response_model=NotificationResponse, response_model_by_alias=True)
async def get_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get a specific notification."""
    service = NotificationService(db)
    notification = await service.get_notification(notification_id)

    if not notification:
        raise NotFoundException(
            detail="Notification not found", error_code="NOTIFICATION_NOT_FOUND"
        )

    if notification.user_id != current_user.id:
        raise ForbiddenException(
            detail="Not authorized to view this notification",
            error_code="NOT_AUTHORIZED_TO_VIEW_THIS_NOTIFICATION",
        )

    return NotificationResponse.model_validate(notification)


@router.post(
    "/",
    response_model=NotificationResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_notification(
    data: NotificationCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create a new notification (admin only)."""
    # TODO: Add admin permission check

    service = NotificationService(db)
    notification = await service.create_notification(
        organization_id=current_user.organization_id,
        title=data.title,
        message=data.message,
        html_content=data.html_content,
        user_id=data.user_id,
        recipient_email=data.recipient_email,
        recipient_phone=data.recipient_phone,
        category=data.category,
        priority=data.priority,
        channels=data.channels,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        entity_reference=data.entity_reference,
        action_url=data.action_url,
        action_label=data.action_label,
        template_id=data.template_id,
        metadata=data.metadata,
        scheduled_at=data.scheduled_at,
        expires_at=data.expires_at,
        created_by=current_user.id,
    )

    return NotificationResponse.model_validate(notification)


@router.post("/send", response_model=NotificationResponse, response_model_by_alias=True)
async def send_from_template(
    data: SendNotificationRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Send a notification using a template."""
    service = NotificationService(db)
    notification = await service.send_from_template(
        template_code=data.template_code,
        organization_id=current_user.organization_id,
        context=data.context,
        user_id=data.user_id,
        recipient_email=data.recipient_email,
        recipient_phone=data.recipient_phone,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        entity_reference=data.entity_reference,
        created_by=current_user.id,
    )

    if not notification:
        raise BadRequestException(
            detail="Failed to send notification. Template may not exist.",
            error_code="FAILED_TO_SEND_NOTIFICATION_TEMPLATE_MAY",
        )

    return NotificationResponse.model_validate(notification)


@router.post("/bulk", status_code=status.HTTP_202_ACCEPTED)
async def send_bulk_notifications(
    data: BulkNotificationRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Send bulk notifications to multiple users."""
    # TODO: Implement bulk notification sending
    # This would typically be handled by a background job

    return {
        "status": "queued",
        "message": "Bulk notifications queued for processing",
    }


@router.post("/mark-read")
async def mark_notifications_read(
    data: MarkReadRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Mark notifications as read."""
    service = NotificationService(db)

    if data.mark_all:
        count = await service.mark_all_as_read(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
        )
        return {"marked_read": count}

    if data.notification_ids:
        count = 0
        for notification_id in data.notification_ids:
            if await service.mark_as_read(notification_id, current_user.id):
                count += 1
        return {"marked_read": count}

    return {"marked_read": 0}


@router.post("/{notification_id}/read")
async def mark_single_notification_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Mark a single notification as read."""
    service = NotificationService(db)
    success = await service.mark_as_read(notification_id, current_user.id)

    if not success:
        raise NotFoundException(
            detail="Notification not found", error_code="NOTIFICATION_NOT_FOUND"
        )

    return {"status": "success"}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Delete (soft) a notification."""
    service = NotificationService(db)
    success = await service.delete_notification(notification_id, current_user.id)

    if not success:
        raise NotFoundException(
            detail="Notification not found", error_code="NOTIFICATION_NOT_FOUND"
        )


@router.put(
    "/preferences/{category}",
    response_model=NotificationPreferenceResponse,
    response_model_by_alias=True,
)
async def update_preference(
    category: NotificationCategory,
    data: NotificationPreferenceUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Update notification preference for a category."""
    service = NotificationService(db)
    preference = await service.update_user_preference(
        user_id=current_user.id,
        category=category,
        organization_id=current_user.organization_id,
        email_enabled=data.email_enabled,
        sms_enabled=data.sms_enabled,
        push_enabled=data.push_enabled,
        in_app_enabled=data.in_app_enabled,
        whatsapp_enabled=data.whatsapp_enabled,
        digest_mode=data.digest_mode,
        digest_frequency=data.digest_frequency,
        quiet_hours_start=data.quiet_hours_start,
        quiet_hours_end=data.quiet_hours_end,
    )
    return NotificationPreferenceResponse.model_validate(preference)
