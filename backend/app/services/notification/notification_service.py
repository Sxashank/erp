"""Notification service for managing system-wide notifications."""

import logging
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    Notification,
    NotificationPreference,
    NotificationLog,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationCategory,
    SysNotificationTemplate,
)
from app.models.auth.user import User
from app.services.email import email_service
from app.services.notification.sms_service import sms_service
from app.services.notification.push_service import push_service

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications."""

    def __init__(self, db: AsyncSession):
        """Initialize notification service."""
        self.db = db

    async def create_notification(
        self,
        organization_id: UUID,
        title: str,
        message: str,
        user_id: Optional[UUID] = None,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        category: NotificationCategory = NotificationCategory.SYSTEM,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        channels: Optional[List[str]] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        entity_reference: Optional[str] = None,
        action_url: Optional[str] = None,
        action_label: Optional[str] = None,
        template_id: Optional[UUID] = None,
        html_content: Optional[str] = None,
        metadata: Optional[dict] = None,
        scheduled_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        created_by: Optional[UUID] = None,
    ) -> Notification:
        """
        Create a new notification.

        Args:
            organization_id: Organization ID
            title: Notification title
            message: Notification message
            user_id: Target user ID (for in-app notifications)
            recipient_email: Email recipient (for non-user notifications)
            recipient_phone: Phone recipient (for SMS notifications)
            category: Notification category
            priority: Notification priority
            channels: Delivery channels (defaults to in_app)
            entity_type: Related entity type
            entity_id: Related entity ID
            entity_reference: Related entity reference
            action_url: URL for action button
            action_label: Label for action button
            template_id: Template ID if using a template
            html_content: HTML content for email
            metadata: Additional metadata
            scheduled_at: Schedule for future delivery
            expires_at: Expiration time
            created_by: User who created the notification

        Returns:
            Created notification
        """
        if channels is None:
            channels = ["in_app"]

        notification = Notification(
            organization_id=organization_id,
            user_id=user_id,
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            template_id=template_id,
            title=title,
            message=message,
            html_content=html_content,
            category=category,
            priority=priority,
            channels=channels,
            status=NotificationStatus.PENDING,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_reference=entity_reference,
            action_url=action_url,
            action_label=action_label,
            metadata=metadata,
            scheduled_at=scheduled_at,
            expires_at=expires_at,
            created_by=created_by,
        )

        self.db.add(notification)
        await self.db.flush()

        # If not scheduled, send immediately
        if not scheduled_at:
            await self.send_notification(notification)

        await self.db.commit()
        await self.db.refresh(notification)

        return notification

    async def send_notification(self, notification: Notification) -> bool:
        """
        Send a notification through configured channels.

        Args:
            notification: Notification to send

        Returns:
            True if at least one channel succeeded
        """
        success = False

        # Check user preferences
        preferences = None
        if notification.user_id:
            preferences = await self._get_user_preferences(
                notification.user_id,
                notification.organization_id,
                notification.category,
            )

        for channel in notification.channels:
            try:
                channel_enum = NotificationChannel(channel)

                # Check if channel is enabled in preferences
                if preferences and not self._is_channel_enabled(preferences, channel_enum):
                    logger.info(
                        f"Channel {channel} disabled for user {notification.user_id}"
                    )
                    continue

                # Send through channel
                channel_success = await self._send_to_channel(notification, channel_enum)

                if channel_success:
                    success = True

                # Log the attempt
                await self._log_delivery(
                    notification.id,
                    channel_enum,
                    NotificationStatus.SENT if channel_success else NotificationStatus.FAILED,
                )

            except Exception as e:
                logger.error(f"Error sending notification via {channel}: {e}")
                await self._log_delivery(
                    notification.id,
                    NotificationChannel(channel),
                    NotificationStatus.FAILED,
                    error_message=str(e),
                )

        # Update notification status
        if success:
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now(timezone.utc)
        else:
            notification.retry_count += 1
            if notification.retry_count >= notification.max_retries:
                notification.status = NotificationStatus.FAILED

        return success

    async def _send_to_channel(
        self,
        notification: Notification,
        channel: NotificationChannel,
    ) -> bool:
        """Send notification through a specific channel."""

        if channel == NotificationChannel.EMAIL:
            return await self._send_email(notification)

        elif channel == NotificationChannel.SMS:
            return await self._send_sms(notification)

        elif channel == NotificationChannel.PUSH:
            return await self._send_push(notification)

        elif channel == NotificationChannel.IN_APP:
            # In-app notifications are already stored
            return True

        elif channel == NotificationChannel.WHATSAPP:
            return await self._send_whatsapp(notification)

        return False

    async def _send_email(self, notification: Notification) -> bool:
        """Send email notification."""
        # Get recipient email
        recipient = notification.recipient_email
        if not recipient and notification.user_id:
            user = await self._get_user(notification.user_id)
            recipient = user.email if user else None

        if not recipient:
            logger.warning(f"No email recipient for notification {notification.id}")
            return False

        html_body = notification.html_content or f"""
        <html>
        <body>
            <h2>{notification.title}</h2>
            <p>{notification.message}</p>
            {f'<p><a href="{notification.action_url}">{notification.action_label or "View Details"}</a></p>' if notification.action_url else ''}
        </body>
        </html>
        """

        return await email_service.send_email(
            to=[recipient],
            subject=notification.title,
            html_body=html_body,
        )

    async def _send_sms(self, notification: Notification) -> bool:
        """Send SMS notification."""
        recipient = notification.recipient_phone
        if not recipient and notification.user_id:
            user = await self._get_user(notification.user_id)
            recipient = user.phone if user and hasattr(user, 'phone') else None

        if not recipient:
            logger.warning(f"No phone number for notification {notification.id}")
            return False

        return await sms_service.send_sms(
            to=recipient,
            message=notification.message,
        )

    async def _send_push(self, notification: Notification) -> bool:
        """Send push notification."""
        if not notification.user_id:
            logger.warning(f"No user ID for push notification {notification.id}")
            return False

        return await push_service.send_push(
            user_id=notification.user_id,
            title=notification.title,
            body=notification.message,
            data={
                "notification_id": str(notification.id),
                "action_url": notification.action_url,
                "category": notification.category.value,
            },
        )

    async def _send_whatsapp(self, notification: Notification) -> bool:
        """Send WhatsApp notification."""
        # WhatsApp integration to be implemented
        logger.info("WhatsApp notifications not yet implemented")
        return False

    async def _get_user(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def _get_user_preferences(
        self,
        user_id: UUID,
        organization_id: UUID,
        category: NotificationCategory,
    ) -> Optional[NotificationPreference]:
        """Get user notification preferences for a category."""
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id,
                NotificationPreference.category == category,
                or_(
                    NotificationPreference.organization_id == organization_id,
                    NotificationPreference.organization_id.is_(None),
                ),
            ).order_by(NotificationPreference.organization_id.desc().nullslast())
        )
        return result.scalar_first()

    def _is_channel_enabled(
        self,
        preference: NotificationPreference,
        channel: NotificationChannel,
    ) -> bool:
        """Check if a channel is enabled in preferences."""
        channel_map = {
            NotificationChannel.EMAIL: preference.email_enabled,
            NotificationChannel.SMS: preference.sms_enabled,
            NotificationChannel.PUSH: preference.push_enabled,
            NotificationChannel.IN_APP: preference.in_app_enabled,
            NotificationChannel.WHATSAPP: preference.whatsapp_enabled,
        }
        return channel_map.get(channel, True)

    async def _log_delivery(
        self,
        notification_id: UUID,
        channel: NotificationChannel,
        status: NotificationStatus,
        error_message: Optional[str] = None,
    ) -> None:
        """Log notification delivery attempt."""
        log = NotificationLog(
            notification_id=notification_id,
            channel=channel,
            status=status,
            response_message=error_message,
        )
        self.db.add(log)

    async def get_notification(self, notification_id: UUID) -> Optional[Notification]:
        """Get notification by ID."""
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def get_user_notifications(
        self,
        user_id: UUID,
        organization_id: UUID,
        category: Optional[NotificationCategory] = None,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Notification], int]:
        """
        Get notifications for a user.

        Args:
            user_id: User ID
            organization_id: Organization ID
            category: Optional category filter
            unread_only: Only return unread notifications
            skip: Pagination offset
            limit: Page size

        Returns:
            Tuple of (notifications list, total count)
        """
        conditions = [
            Notification.user_id == user_id,
            Notification.organization_id == organization_id,
            Notification.is_active == True,
        ]

        if category:
            conditions.append(Notification.category == category)

        if unread_only:
            conditions.append(Notification.read_at.is_(None))

        # Count query
        count_result = await self.db.execute(
            select(func.count()).select_from(Notification).where(and_(*conditions))
        )
        total = count_result.scalar()

        # Data query
        result = await self.db.execute(
            select(Notification)
            .where(and_(*conditions))
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        notifications = list(result.scalars().all())

        return notifications, total

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Mark notification as read."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()

        if notification:
            notification.read_at = datetime.now(timezone.utc)
            notification.status = NotificationStatus.READ
            await self.db.commit()
            return True

        return False

    async def mark_all_as_read(self, user_id: UUID, organization_id: UUID) -> int:
        """Mark all notifications as read for a user."""
        from sqlalchemy import update

        result = await self.db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.organization_id == organization_id,
                Notification.read_at.is_(None),
            )
            .values(
                read_at=datetime.now(timezone.utc),
                status=NotificationStatus.READ,
            )
        )
        await self.db.commit()
        return result.rowcount

    async def get_unread_count(self, user_id: UUID, organization_id: UUID) -> int:
        """Get count of unread notifications for a user."""
        result = await self.db.execute(
            select(func.count()).select_from(Notification).where(
                Notification.user_id == user_id,
                Notification.organization_id == organization_id,
                Notification.read_at.is_(None),
                Notification.is_active == True,
            )
        )
        return result.scalar() or 0

    async def delete_notification(
        self,
        notification_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Soft delete a notification."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()

        if notification:
            notification.soft_delete(user_id)
            await self.db.commit()
            return True

        return False

    # Template-based notification methods
    async def send_from_template(
        self,
        template_code: str,
        organization_id: UUID,
        context: dict,
        user_id: Optional[UUID] = None,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        entity_reference: Optional[str] = None,
        created_by: Optional[UUID] = None,
    ) -> Optional[Notification]:
        """
        Send notification using a template.

        Args:
            template_code: Template code
            organization_id: Organization ID
            context: Template variable values
            user_id: Target user ID
            recipient_email: Email recipient
            recipient_phone: Phone recipient
            entity_type: Related entity type
            entity_id: Related entity ID
            entity_reference: Related entity reference
            created_by: User creating the notification

        Returns:
            Created notification or None if template not found
        """
        # Get template
        template = await self._get_template(template_code, organization_id)
        if not template:
            logger.error(f"Template not found: {template_code}")
            return None

        # Render template content
        title = self._render_template(template.in_app_title or template.name, context)
        message = self._render_template(template.in_app_message or "", context)
        html_content = self._render_template(template.email_body_html or "", context)

        return await self.create_notification(
            organization_id=organization_id,
            title=title,
            message=message,
            html_content=html_content,
            user_id=user_id,
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            category=template.category,
            priority=NotificationPriority.MEDIUM,
            channels=template.channels,
            template_id=template.id,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_reference=entity_reference,
            created_by=created_by,
        )

    async def _get_template(
        self,
        code: str,
        organization_id: UUID,
    ) -> Optional[SysNotificationTemplate]:
        """Get notification template by code."""
        # First try org-specific template
        result = await self.db.execute(
            select(SysNotificationTemplate).where(
                SysNotificationTemplate.code == code,
                SysNotificationTemplate.organization_id == organization_id,
                SysNotificationTemplate.is_active == True,
            )
        )
        template = result.scalar_one_or_none()

        if not template:
            # Fall back to global template
            result = await self.db.execute(
                select(SysNotificationTemplate).where(
                    SysNotificationTemplate.code == code,
                    SysNotificationTemplate.organization_id.is_(None),
                    SysNotificationTemplate.is_active == True,
                )
            )
            template = result.scalar_one_or_none()

        return template

    def _render_template(self, template: str, context: dict) -> str:
        """Render template string with context values."""
        result = template
        for key, value in context.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value) if value is not None else "")
        return result

    # User preferences methods
    async def get_user_preferences(
        self,
        user_id: UUID,
        organization_id: Optional[UUID] = None,
    ) -> List[NotificationPreference]:
        """Get all notification preferences for a user."""
        conditions = [NotificationPreference.user_id == user_id]
        if organization_id:
            conditions.append(
                or_(
                    NotificationPreference.organization_id == organization_id,
                    NotificationPreference.organization_id.is_(None),
                )
            )

        result = await self.db.execute(
            select(NotificationPreference).where(and_(*conditions))
        )
        return list(result.scalars().all())

    async def update_user_preference(
        self,
        user_id: UUID,
        category: NotificationCategory,
        organization_id: Optional[UUID] = None,
        email_enabled: Optional[bool] = None,
        sms_enabled: Optional[bool] = None,
        push_enabled: Optional[bool] = None,
        in_app_enabled: Optional[bool] = None,
        whatsapp_enabled: Optional[bool] = None,
        digest_mode: Optional[bool] = None,
        digest_frequency: Optional[str] = None,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
    ) -> NotificationPreference:
        """Update or create user notification preference."""
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id,
                NotificationPreference.category == category,
                NotificationPreference.organization_id == organization_id
                if organization_id
                else NotificationPreference.organization_id.is_(None),
            )
        )
        preference = result.scalar_one_or_none()

        if not preference:
            preference = NotificationPreference(
                user_id=user_id,
                category=category,
                organization_id=organization_id,
            )
            self.db.add(preference)

        # Update fields if provided
        if email_enabled is not None:
            preference.email_enabled = email_enabled
        if sms_enabled is not None:
            preference.sms_enabled = sms_enabled
        if push_enabled is not None:
            preference.push_enabled = push_enabled
        if in_app_enabled is not None:
            preference.in_app_enabled = in_app_enabled
        if whatsapp_enabled is not None:
            preference.whatsapp_enabled = whatsapp_enabled
        if digest_mode is not None:
            preference.digest_mode = digest_mode
        if digest_frequency is not None:
            preference.digest_frequency = digest_frequency
        if quiet_hours_start is not None:
            preference.quiet_hours_start = quiet_hours_start
        if quiet_hours_end is not None:
            preference.quiet_hours_end = quiet_hours_end

        await self.db.commit()
        await self.db.refresh(preference)
        return preference
