"""Portal Notification Service.

Handles notifications, messages, and support tickets.
"""

import json
import secrets
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.portal.communication import (
    PortalAnnouncement,
    PortalMessage,
    PortalNotification,
    PortalTicket,
)
from app.models.portal.enums import (
    NotificationChannel,
    NotificationPriority,
    PortalUserStatus,
    TicketCategory,
    TicketPriority,
    TicketStatus,
)
from app.models.portal.portal_user import PortalUser
from app.models.portal.portal_user_entity import PortalUserEntity
from app.services.notification.communication_service import (
    Channel,
    DispatchStatus,
    Recipient,
    communication_service,
)


class PortalNotificationService:
    """Portal notification service."""

    # Default SLA hours by priority
    TICKET_SLA_HOURS = {
        TicketPriority.CRITICAL: 4,
        TicketPriority.HIGH: 8,
        TicketPriority.MEDIUM: 24,
        TicketPriority.LOW: 48,
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Notifications
    # =========================================================================

    async def create_notification(
        self,
        organization_id: UUID,
        user_id: UUID,
        title: str,
        body: str,
        notification_type: str,
        channel: NotificationChannel = NotificationChannel.IN_APP,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        action_url: str | None = None,
        action_data: dict[str, Any] | None = None,
        reference_type: str | None = None,
        reference_id: UUID | None = None,
        expires_at: datetime | None = None,
    ) -> PortalNotification:
        """Create a notification for a user."""
        notification = PortalNotification(
            organization_id=organization_id,
            user_id=user_id,
            title=title,
            body=body,
            notification_type=notification_type,
            channel=channel,
            priority=priority,
            action_url=action_url,
            action_data=action_data,
            reference_type=reference_type,
            reference_id=reference_id,
            expires_at=expires_at,
        )
        self.db.add(notification)
        await self.db.flush()

        if channel == NotificationChannel.IN_APP:
            notification.is_sent = True
            notification.sent_at = datetime.utcnow()
            notification.delivery_status = "IN_APP"
            return notification

        if channel in [
            NotificationChannel.PUSH,
            NotificationChannel.SMS,
            NotificationChannel.EMAIL,
        ]:
            await self._send_notification(notification)

        return notification

    async def get_notifications(
        self,
        user_id: UUID,
        is_read: bool | None = None,
        notification_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """Get notifications for a user."""
        stmt = select(PortalNotification).where(PortalNotification.user_id == user_id)

        if is_read is not None:
            stmt = stmt.where(PortalNotification.is_read == is_read)

        if notification_type:
            stmt = stmt.where(PortalNotification.notification_type == notification_type)

        # Exclude expired
        stmt = stmt.where(
            or_(
                PortalNotification.expires_at.is_(None),
                PortalNotification.expires_at > datetime.utcnow(),
            )
        )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated results
        stmt = stmt.order_by(PortalNotification.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)
        notifications = list(result.scalars().all())

        items = [
            {
                "id": str(n.id),
                "title": n.title,
                "body": n.body,
                "notification_type": n.notification_type,
                "channel": n.channel.value if hasattr(n.channel, "value") else n.channel,
                "priority": n.priority.value if hasattr(n.priority, "value") else n.priority,
                "action_url": n.action_url,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ]

        return items, total

    async def mark_as_read(
        self,
        notification_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Mark a notification as read."""
        stmt = select(PortalNotification).where(
            and_(
                PortalNotification.id == notification_id,
                PortalNotification.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        notification = result.scalar_one_or_none()

        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            return True
        return False

    async def mark_all_as_read(
        self,
        user_id: UUID,
    ) -> int:
        """Mark all notifications as read for a user."""
        stmt = (
            update(PortalNotification)
            .where(
                and_(
                    PortalNotification.user_id == user_id,
                    PortalNotification.is_read == False,
                )
            )
            .values(is_read=True, read_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        return result.rowcount

    async def get_unread_count(
        self,
        user_id: UUID,
    ) -> int:
        """Get unread notification count."""
        stmt = select(func.count()).where(
            and_(
                PortalNotification.user_id == user_id,
                PortalNotification.is_read == False,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar()

    async def notify_entity_borrowers(
        self,
        *,
        organization_id: UUID,
        entity_id: UUID,
        title: str,
        body: str,
        notification_type: str,
        action_url: str | None = None,
        reference_type: str | None = None,
        reference_id: UUID | None = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
    ) -> int:
        """Create one in-app notification per active borrower linked to an entity."""
        stmt = (
            select(PortalUser.id)
            .join(
                PortalUserEntity,
                PortalUserEntity.portal_user_id == PortalUser.id,
            )
            .where(
                PortalUser.organization_id == organization_id,
                PortalUser.status == PortalUserStatus.ACTIVE.value,
                PortalUser.deleted_at.is_(None),
                PortalUserEntity.entity_id == entity_id,
                PortalUserEntity.organization_id == organization_id,
                PortalUserEntity.is_link_active.is_(True),
                PortalUserEntity.deleted_at.is_(None),
            )
        )
        user_ids = [row[0] for row in (await self.db.execute(stmt)).all()]
        for user_id in user_ids:
            await self.create_notification(
                organization_id=organization_id,
                user_id=user_id,
                title=title,
                body=body,
                notification_type=notification_type,
                channel=NotificationChannel.IN_APP,
                priority=priority,
                action_url=action_url,
                reference_type=reference_type,
                reference_id=reference_id,
            )
        return len(user_ids)

    async def notify_roles(
        self,
        *,
        organization_id: UUID,
        actor_roles: list[str],
        title: str,
        body: str,
        notification_type: str,
        action_url: str | None = None,
        reference_type: str | None = None,
        reference_id: UUID | None = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
    ) -> int:
        """Create one in-app notification per active internal actor role."""
        if not actor_roles:
            return 0
        stmt = select(PortalUser.id).where(
            PortalUser.organization_id == organization_id,
            PortalUser.actor_role.in_(actor_roles),
            PortalUser.status == PortalUserStatus.ACTIVE.value,
            PortalUser.deleted_at.is_(None),
        )
        user_ids = [row[0] for row in (await self.db.execute(stmt)).all()]
        for user_id in user_ids:
            await self.create_notification(
                organization_id=organization_id,
                user_id=user_id,
                title=title,
                body=body,
                notification_type=notification_type,
                channel=NotificationChannel.IN_APP,
                priority=priority,
                action_url=action_url,
                reference_type=reference_type,
                reference_id=reference_id,
            )
        return len(user_ids)

    # =========================================================================
    # Messages
    # =========================================================================

    async def send_message(
        self,
        organization_id: UUID,
        user_id: UUID,
        subject: str | None,
        body: str,
        thread_id: UUID | None = None,
        parent_message_id: UUID | None = None,
        reference_type: str | None = None,
        reference_id: UUID | None = None,
        attachment_ids: list[UUID] | None = None,
    ) -> PortalMessage:
        """Send a message from customer."""
        # Generate thread ID if new conversation
        if not thread_id and not parent_message_id:
            thread_id = UUID(secrets.token_hex(16))

        message = PortalMessage(
            organization_id=organization_id,
            user_id=user_id,
            thread_id=thread_id,
            parent_message_id=parent_message_id,
            subject=subject,
            body=body,
            is_from_customer=True,
            has_attachments=bool(attachment_ids),
            attachment_ids=str(attachment_ids) if attachment_ids else None,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        self.db.add(message)

        return message

    async def get_messages(
        self,
        user_id: UUID,
        thread_id: UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """Get messages for a user."""
        if thread_id:
            # Get messages in a specific thread
            stmt = (
                select(PortalMessage)
                .where(
                    and_(
                        PortalMessage.user_id == user_id,
                        PortalMessage.thread_id == thread_id,
                    )
                )
                .order_by(PortalMessage.created_at.asc())
            )
        else:
            # Get latest message from each thread
            stmt = (
                select(PortalMessage)
                .where(PortalMessage.user_id == user_id)
                .order_by(PortalMessage.created_at.desc())
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated results
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)
        messages = list(result.scalars().all())

        items = [
            {
                "id": str(m.id),
                "thread_id": str(m.thread_id) if m.thread_id else None,
                "subject": m.subject,
                "body": m.body,
                "is_from_customer": m.is_from_customer,
                "sender_name": m.sender_name,
                "is_read": m.is_read,
                "has_attachments": m.has_attachments,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ]

        return items, total

    async def mark_message_read(
        self,
        message_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Mark a message as read."""
        stmt = select(PortalMessage).where(
            and_(
                PortalMessage.id == message_id,
                PortalMessage.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        message = result.scalar_one_or_none()

        if message:
            message.is_read = True
            message.read_at = datetime.utcnow()
            return True
        return False

    # =========================================================================
    # Support Tickets
    # =========================================================================

    async def create_ticket(
        self,
        organization_id: UUID,
        user_id: UUID,
        subject: str,
        description: str,
        category: TicketCategory,
        priority: TicketPriority = TicketPriority.MEDIUM,
        sub_category: str | None = None,
        loan_account_id: UUID | None = None,
        related_payment_id: UUID | None = None,
        related_service_request_id: UUID | None = None,
    ) -> PortalTicket:
        """Create a support ticket."""
        ticket_number = self._generate_ticket_number()

        ticket = PortalTicket(
            organization_id=organization_id,
            user_id=user_id,
            ticket_number=ticket_number,
            subject=subject,
            description=description,
            category=category,
            sub_category=sub_category,
            priority=priority,
            status=TicketStatus.OPEN,
            loan_account_id=loan_account_id,
            related_payment_id=related_payment_id,
            related_service_request_id=related_service_request_id,
            sla_due_at=datetime.utcnow() + timedelta(hours=self.TICKET_SLA_HOURS.get(priority, 24)),
        )
        self.db.add(ticket)

        # Create notification for support team
        # await self._notify_support_team(ticket)

        return ticket

    async def get_tickets(
        self,
        user_id: UUID,
        status: TicketStatus | None = None,
        category: TicketCategory | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """Get support tickets for a user."""
        stmt = select(PortalTicket).where(PortalTicket.user_id == user_id)

        if status:
            stmt = stmt.where(PortalTicket.status == status)

        if category:
            stmt = stmt.where(PortalTicket.category == category)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated results
        stmt = stmt.order_by(PortalTicket.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)
        tickets = list(result.scalars().all())

        items = [
            {
                "id": str(t.id),
                "ticket_number": t.ticket_number,
                "subject": t.subject,
                "category": t.category.value,
                "priority": t.priority.value,
                "status": t.status.value,
                "created_at": t.created_at.isoformat(),
                "sla_due_at": t.sla_due_at.isoformat() if t.sla_due_at else None,
                "is_sla_breached": t.is_sla_breached,
            }
            for t in tickets
        ]

        return items, total

    async def get_ticket_details(
        self,
        ticket_id: UUID,
        user_id: UUID,
    ) -> dict[str, Any] | None:
        """Get ticket details."""
        stmt = select(PortalTicket).where(
            and_(
                PortalTicket.id == ticket_id,
                PortalTicket.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        ticket = result.scalar_one_or_none()

        if not ticket:
            return None

        # Get related messages
        messages_stmt = (
            select(PortalMessage)
            .where(
                and_(
                    PortalMessage.reference_type == "TICKET",
                    PortalMessage.reference_id == ticket_id,
                )
            )
            .order_by(PortalMessage.created_at.asc())
        )
        messages_result = await self.db.execute(messages_stmt)
        messages = list(messages_result.scalars().all())

        return {
            "id": str(ticket.id),
            "ticket_number": ticket.ticket_number,
            "subject": ticket.subject,
            "description": ticket.description,
            "category": ticket.category.value,
            "sub_category": ticket.sub_category,
            "priority": ticket.priority.value,
            "status": ticket.status.value,
            "created_at": ticket.created_at.isoformat(),
            "sla_due_at": ticket.sla_due_at.isoformat() if ticket.sla_due_at else None,
            "is_sla_breached": ticket.is_sla_breached,
            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
            "resolution_summary": ticket.resolution_summary,
            "customer_rating": ticket.customer_rating,
            "customer_feedback": ticket.customer_feedback,
            "messages": [
                {
                    "id": str(m.id),
                    "body": m.body,
                    "is_from_customer": m.is_from_customer,
                    "sender_name": m.sender_name,
                    "created_at": m.created_at.isoformat(),
                }
                for m in messages
            ],
        }

    async def add_ticket_reply(
        self,
        ticket_id: UUID,
        user_id: UUID,
        message: str,
        attachment_ids: list[UUID] | None = None,
    ) -> PortalMessage | None:
        """Add a reply to a ticket."""
        stmt = select(PortalTicket).where(
            and_(
                PortalTicket.id == ticket_id,
                PortalTicket.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        ticket = result.scalar_one_or_none()

        if not ticket:
            return None

        if ticket.status in [TicketStatus.CLOSED]:
            raise ValueError("Cannot reply to a closed ticket")

        # Reopen if resolved
        if ticket.status == TicketStatus.RESOLVED:
            ticket.status = TicketStatus.REOPENED

        reply = PortalMessage(
            organization_id=ticket.organization_id,
            user_id=user_id,
            body=message,
            is_from_customer=True,
            has_attachments=bool(attachment_ids),
            attachment_ids=str(attachment_ids) if attachment_ids else None,
            reference_type="TICKET",
            reference_id=ticket_id,
        )
        self.db.add(reply)

        return reply

    async def rate_ticket(
        self,
        ticket_id: UUID,
        user_id: UUID,
        rating: int,
        feedback: str | None = None,
    ) -> bool:
        """Rate a resolved/closed ticket."""
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        stmt = select(PortalTicket).where(
            and_(
                PortalTicket.id == ticket_id,
                PortalTicket.user_id == user_id,
                PortalTicket.status.in_([TicketStatus.RESOLVED, TicketStatus.CLOSED]),
            )
        )
        result = await self.db.execute(stmt)
        ticket = result.scalar_one_or_none()

        if not ticket:
            return False

        ticket.customer_rating = rating
        ticket.customer_feedback = feedback
        ticket.feedback_at = datetime.utcnow()

        return True

    # =========================================================================
    # Announcements
    # =========================================================================

    async def get_active_announcements(
        self,
        organization_id: UUID,
        user_segment: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get active announcements."""
        now = datetime.utcnow()

        stmt = select(PortalAnnouncement).where(
            and_(
                PortalAnnouncement.organization_id == organization_id,
                PortalAnnouncement.is_active == True,
                PortalAnnouncement.start_date <= now,
                or_(
                    PortalAnnouncement.end_date.is_(None),
                    PortalAnnouncement.end_date > now,
                ),
            )
        )

        result = await self.db.execute(stmt)
        announcements = list(result.scalars().all())

        return [
            {
                "id": str(a.id),
                "title": a.title,
                "body": a.body,
                "announcement_type": a.announcement_type,
                "display_position": a.display_position,
                "action_url": a.action_url,
                "action_text": a.action_text,
                "is_dismissible": a.is_dismissible,
            }
            for a in announcements
        ]

    async def record_announcement_view(
        self,
        announcement_id: UUID,
    ):
        """Record announcement view."""
        stmt = select(PortalAnnouncement).where(PortalAnnouncement.id == announcement_id)
        result = await self.db.execute(stmt)
        announcement = result.scalar_one_or_none()

        if announcement:
            announcement.view_count += 1

    async def record_announcement_dismiss(
        self,
        announcement_id: UUID,
    ):
        """Record announcement dismiss."""
        stmt = select(PortalAnnouncement).where(PortalAnnouncement.id == announcement_id)
        result = await self.db.execute(stmt)
        announcement = result.scalar_one_or_none()

        if announcement:
            announcement.dismiss_count += 1

    async def record_announcement_click(
        self,
        announcement_id: UUID,
    ):
        """Record announcement action click."""
        stmt = select(PortalAnnouncement).where(PortalAnnouncement.id == announcement_id)
        result = await self.db.execute(stmt)
        announcement = result.scalar_one_or_none()

        if announcement:
            announcement.click_count += 1

    # =========================================================================
    # Notification Templates
    # =========================================================================

    async def send_payment_due_reminder(
        self,
        organization_id: UUID,
        user_id: UUID,
        loan_account_number: str,
        due_date: str,
        amount: float,
    ):
        """Send payment due reminder notification."""
        await self.create_notification(
            organization_id=organization_id,
            user_id=user_id,
            title="Payment Due Reminder",
            body=f"Your EMI payment of ₹{amount:,.2f} for loan {loan_account_number} is due on {due_date}.",
            notification_type="PAYMENT_DUE",
            channel=NotificationChannel.PUSH,
            priority=NotificationPriority.HIGH,
            action_url=f"/payments?loan={loan_account_number}",
        )

    async def send_payment_success_notification(
        self,
        organization_id: UUID,
        user_id: UUID,
        loan_account_number: str,
        amount: float,
        receipt_number: str,
    ):
        """Send payment success notification."""
        await self.create_notification(
            organization_id=organization_id,
            user_id=user_id,
            title="Payment Successful",
            body=f"Your payment of ₹{amount:,.2f} for loan {loan_account_number} has been received. Receipt: {receipt_number}",
            notification_type="PAYMENT_SUCCESS",
            channel=NotificationChannel.PUSH,
            priority=NotificationPriority.MEDIUM,
        )

    async def send_service_request_update(
        self,
        organization_id: UUID,
        user_id: UUID,
        request_number: str,
        status: str,
        message: str,
    ):
        """Send service request status update."""
        await self.create_notification(
            organization_id=organization_id,
            user_id=user_id,
            title=f"Service Request Update - {request_number}",
            body=message,
            notification_type="SERVICE_REQUEST_UPDATE",
            channel=NotificationChannel.IN_APP,
            priority=NotificationPriority.MEDIUM,
            action_url=f"/service-requests/{request_number}",
        )

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _generate_ticket_number(self) -> str:
        """Generate unique ticket number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(3).upper()
        return f"TKT{timestamp}{random_suffix}"

    async def _send_notification(
        self,
        notification: PortalNotification,
    ):
        """Send notification via appropriate channel."""
        user = await self._get_portal_user(notification.user_id)
        if user is None:
            notification.delivery_status = "FAILED"
            notification.delivery_error = "Portal user not found"
            notification.is_sent = False
            return

        if not self._is_channel_enabled_for_user(user, notification.channel):
            notification.delivery_status = "DISABLED_BY_PREFERENCE"
            notification.delivery_error = None
            notification.is_sent = False
            return

        result = await communication_service.send(
            channel=self._to_channel(notification.channel),
            recipient=self._to_recipient(user, notification.channel),
            template_code=notification.notification_type,
            context=self._build_dispatch_context(notification),
        )
        notification.delivery_status = result.status.value.upper()
        notification.delivery_error = result.error
        notification.is_sent = result.status in {
            DispatchStatus.SENT,
            DispatchStatus.QUEUED,
            DispatchStatus.MOCKED,
        }
        notification.sent_at = datetime.utcnow() if notification.is_sent else None

    async def _send_push_notification(
        self,
        notification: PortalNotification,
    ):
        """Send push notification via FCM/APNS."""
        await self._send_notification(notification)

    async def _send_sms_notification(
        self,
        notification: PortalNotification,
    ):
        """Send SMS notification."""
        await self._send_notification(notification)

    async def _send_email_notification(
        self,
        notification: PortalNotification,
    ):
        """Send email notification."""
        await self._send_notification(notification)

    async def _get_portal_user(self, user_id: UUID) -> PortalUser | None:
        stmt = (
            select(PortalUser)
            .options(selectinload(PortalUser.devices))
            .where(
                PortalUser.id == user_id,
                PortalUser.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _is_channel_enabled_for_user(
        self,
        user: PortalUser,
        channel: NotificationChannel,
    ) -> bool:
        if channel == NotificationChannel.IN_APP:
            return True
        raw = user.notification_preferences
        if not raw:
            return True
        try:
            preferences = json.loads(raw) if isinstance(raw, str) else raw
        except (TypeError, ValueError):
            return True
        if not isinstance(preferences, dict):
            return True
        key_map = {
            NotificationChannel.SMS: "sms",
            NotificationChannel.EMAIL: "email",
            NotificationChannel.PUSH: "push",
            NotificationChannel.WHATSAPP: "whatsapp",
        }
        key = key_map.get(channel)
        if not key:
            return True
        value = preferences.get(key)
        return True if value is None else bool(value)

    def _to_channel(self, channel: NotificationChannel) -> Channel:
        mapping = {
            NotificationChannel.SMS: Channel.SMS,
            NotificationChannel.EMAIL: Channel.EMAIL,
            NotificationChannel.PUSH: Channel.PUSH,
            NotificationChannel.IN_APP: Channel.IN_APP,
        }
        try:
            return mapping[channel]
        except KeyError as exc:
            raise ValueError(f"Unsupported portal notification channel: {channel}") from exc

    def _to_recipient(
        self,
        user: PortalUser,
        channel: NotificationChannel,
    ) -> Recipient:
        latest_device = None
        active_devices = [
            device for device in user.devices if device.is_active and not device.blocked_at
        ]
        if active_devices:
            active_devices.sort(key=lambda item: item.last_seen_at, reverse=True)
            latest_device = active_devices[0]
        return Recipient(
            user_id=str(user.id),
            email=user.email,
            phone=user.mobile,
            device_token=(
                (latest_device.fcm_token or latest_device.apns_token)
                if latest_device is not None
                else None
            ),
        )

    def _build_dispatch_context(
        self,
        notification: PortalNotification,
    ) -> dict[str, Any]:
        html_body = (
            "<html><body>"
            f"<h2>{notification.title}</h2>"
            f"<p>{notification.body}</p>"
            + (
                f'<p><a href="{notification.action_url}">Open portal</a></p>'
                if notification.action_url
                else ""
            )
            + "</body></html>"
        )
        return {
            "title": notification.title,
            "subject": notification.title,
            "message": notification.body,
            "body": notification.body,
            "html_body": html_body,
            "data": {
                "notification_id": str(notification.id),
                "reference_type": notification.reference_type,
                "reference_id": (
                    str(notification.reference_id) if notification.reference_id else None
                ),
                "action_url": notification.action_url,
            },
        }
