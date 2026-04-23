"""Portal Notification Service.

Handles notifications, messages, and support tickets.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portal.communication import (
    PortalNotification,
    PortalMessage,
    PortalTicket,
    PortalAnnouncement,
)
from app.models.portal.enums import (
    NotificationChannel,
    NotificationPriority,
    TicketStatus,
    TicketPriority,
    TicketCategory,
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
        action_url: Optional[str] = None,
        action_data: Optional[str] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[UUID] = None,
        expires_at: Optional[datetime] = None,
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

        # Send push notification if applicable
        if channel in [NotificationChannel.PUSH, NotificationChannel.SMS, NotificationChannel.EMAIL]:
            await self._send_notification(notification)

        return notification

    async def get_notifications(
        self,
        user_id: UUID,
        is_read: Optional[bool] = None,
        notification_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get notifications for a user."""
        stmt = select(PortalNotification).where(
            PortalNotification.user_id == user_id
        )

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
                "channel": n.channel.value,
                "priority": n.priority.value,
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

    # =========================================================================
    # Messages
    # =========================================================================

    async def send_message(
        self,
        organization_id: UUID,
        user_id: UUID,
        subject: Optional[str],
        body: str,
        thread_id: Optional[UUID] = None,
        parent_message_id: Optional[UUID] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[UUID] = None,
        attachment_ids: Optional[List[UUID]] = None,
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
        thread_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
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
        sub_category: Optional[str] = None,
        loan_account_id: Optional[UUID] = None,
        related_payment_id: Optional[UUID] = None,
        related_service_request_id: Optional[UUID] = None,
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
            sla_due_at=datetime.utcnow() + timedelta(
                hours=self.TICKET_SLA_HOURS.get(priority, 24)
            ),
        )
        self.db.add(ticket)

        # Create notification for support team
        # await self._notify_support_team(ticket)

        return ticket

    async def get_tickets(
        self,
        user_id: UUID,
        status: Optional[TicketStatus] = None,
        category: Optional[TicketCategory] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
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
    ) -> Optional[Dict[str, Any]]:
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
        attachment_ids: Optional[List[UUID]] = None,
    ) -> Optional[PortalMessage]:
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
        feedback: Optional[str] = None,
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
        user_segment: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
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
        stmt = select(PortalAnnouncement).where(
            PortalAnnouncement.id == announcement_id
        )
        result = await self.db.execute(stmt)
        announcement = result.scalar_one_or_none()

        if announcement:
            announcement.view_count += 1

    async def record_announcement_dismiss(
        self,
        announcement_id: UUID,
    ):
        """Record announcement dismiss."""
        stmt = select(PortalAnnouncement).where(
            PortalAnnouncement.id == announcement_id
        )
        result = await self.db.execute(stmt)
        announcement = result.scalar_one_or_none()

        if announcement:
            announcement.dismiss_count += 1

    async def record_announcement_click(
        self,
        announcement_id: UUID,
    ):
        """Record announcement action click."""
        stmt = select(PortalAnnouncement).where(
            PortalAnnouncement.id == announcement_id
        )
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
        if notification.channel == NotificationChannel.PUSH:
            await self._send_push_notification(notification)
        elif notification.channel == NotificationChannel.SMS:
            await self._send_sms_notification(notification)
        elif notification.channel == NotificationChannel.EMAIL:
            await self._send_email_notification(notification)

        notification.is_sent = True
        notification.sent_at = datetime.utcnow()

    async def _send_push_notification(
        self,
        notification: PortalNotification,
    ):
        """Send push notification via FCM/APNS."""
        # This would integrate with Firebase Cloud Messaging
        # Placeholder implementation
        notification.delivery_status = "SENT"

    async def _send_sms_notification(
        self,
        notification: PortalNotification,
    ):
        """Send SMS notification."""
        # This would integrate with SMS gateway
        # Placeholder implementation
        notification.delivery_status = "SENT"

    async def _send_email_notification(
        self,
        notification: PortalNotification,
    ):
        """Send email notification."""
        # This would integrate with email service
        # Placeholder implementation
        notification.delivery_status = "SENT"
