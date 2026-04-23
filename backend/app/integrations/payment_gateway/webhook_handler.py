"""Payment Gateway Webhook Handler."""

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.payment_gateway.base import (
    PaymentGateway,
    PaymentStatus,
    PaymentMethod,
)


logger = logging.getLogger(__name__)


class WebhookEventType(str, Enum):
    """Webhook event types."""
    # Payment events
    PAYMENT_AUTHORIZED = "payment.authorized"
    PAYMENT_CAPTURED = "payment.captured"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_PENDING = "payment.pending"

    # Refund events
    REFUND_CREATED = "refund.created"
    REFUND_PROCESSED = "refund.processed"
    REFUND_FAILED = "refund.failed"

    # Order events
    ORDER_PAID = "order.paid"

    # Payment Link events
    PAYMENT_LINK_PAID = "payment_link.paid"
    PAYMENT_LINK_EXPIRED = "payment_link.expired"
    PAYMENT_LINK_CANCELLED = "payment_link.cancelled"

    # QR code events
    QR_CODE_CLOSED = "qr_code.closed"

    # Subscription events
    SUBSCRIPTION_ACTIVATED = "subscription.activated"
    SUBSCRIPTION_CHARGED = "subscription.charged"
    SUBSCRIPTION_PENDING = "subscription.pending"
    SUBSCRIPTION_HALTED = "subscription.halted"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    SUBSCRIPTION_PAUSED = "subscription.paused"
    SUBSCRIPTION_RESUMED = "subscription.resumed"

    # Mandate events (NACH/UPI AutoPay)
    TOKEN_CONFIRMED = "token.confirmed"
    TOKEN_REJECTED = "token.rejected"
    TOKEN_PAUSED = "token.paused"
    TOKEN_CANCELLED = "token.cancelled"


@dataclass
class WebhookEvent:
    """Parsed webhook event."""
    event_type: WebhookEventType
    event_id: str
    account_id: str
    created_at: datetime
    payload: Dict[str, Any]
    # Extracted fields
    payment_id: Optional[str] = None
    order_id: Optional[str] = None
    refund_id: Optional[str] = None
    amount: Optional[Decimal] = None
    status: Optional[str] = None
    method: Optional[str] = None
    notes: Dict[str, str] = None
    # Our tracking IDs from notes
    organization_id: Optional[UUID] = None
    loan_account_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    receipt_id: Optional[str] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = {}


# Type for event handlers
EventHandler = Callable[[WebhookEvent, AsyncSession], Awaitable[bool]]


class PaymentWebhookHandler:
    """
    Handles payment gateway webhooks.

    Supports:
    - Signature verification
    - Event parsing
    - Event dispatch to handlers
    - Idempotency checking
    - Error handling and logging
    """

    def __init__(
        self,
        gateway: PaymentGateway,
        db: Optional[AsyncSession] = None,
    ):
        """
        Initialize webhook handler.

        Args:
            gateway: Payment gateway instance
            db: Database session for persistence
        """
        self.gateway = gateway
        self.db = db
        self._handlers: Dict[WebhookEventType, List[EventHandler]] = {}
        self._processed_events: set = set()  # In-memory for demo; use DB in production

    def register_handler(
        self, event_type: WebhookEventType, handler: EventHandler
    ) -> None:
        """Register a handler for an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def register_handlers(
        self, handlers: Dict[WebhookEventType, EventHandler]
    ) -> None:
        """Register multiple handlers."""
        for event_type, handler in handlers.items():
            self.register_handler(event_type, handler)

    async def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature."""
        return await self.gateway.verify_webhook_signature(payload, signature)

    def parse_event(self, payload: Dict[str, Any]) -> WebhookEvent:
        """Parse webhook payload into WebhookEvent."""
        event_type_str = payload.get("event")
        try:
            event_type = WebhookEventType(event_type_str)
        except ValueError:
            raise ValueError(f"Unknown event type: {event_type_str}")

        # Extract common fields
        entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        if not entity:
            entity = payload.get("payload", {}).get("refund", {}).get("entity", {})
        if not entity:
            entity = payload.get("payload", {}).get("order", {}).get("entity", {})
        if not entity:
            entity = payload.get("payload", {}).get("payment_link", {}).get("entity", {})
        if not entity:
            entity = payload.get("payload", {}).get("subscription", {}).get("entity", {})
        if not entity:
            entity = payload.get("payload", {}).get("token", {}).get("entity", {})

        notes = entity.get("notes", {})

        # Extract our tracking IDs from notes
        org_id = None
        loan_id = None
        cust_id = None
        if notes.get("organization_id"):
            try:
                org_id = UUID(notes["organization_id"])
            except (ValueError, TypeError):
                pass
        if notes.get("loan_account_id"):
            try:
                loan_id = UUID(notes["loan_account_id"])
            except (ValueError, TypeError):
                pass
        if notes.get("customer_id"):
            try:
                cust_id = UUID(notes["customer_id"])
            except (ValueError, TypeError):
                pass

        return WebhookEvent(
            event_type=event_type,
            event_id=payload.get("event_id", ""),
            account_id=payload.get("account_id", ""),
            created_at=datetime.fromtimestamp(payload.get("created_at", 0)),
            payload=payload,
            payment_id=entity.get("id"),
            order_id=entity.get("order_id"),
            refund_id=entity.get("id") if "refund" in event_type_str else None,
            amount=Decimal(entity.get("amount", 0)) / 100 if entity.get("amount") else None,
            status=entity.get("status"),
            method=entity.get("method"),
            notes=notes,
            organization_id=org_id,
            loan_account_id=loan_id,
            customer_id=cust_id,
            receipt_id=entity.get("receipt") or notes.get("receipt_id"),
        )

    async def is_processed(self, event_id: str) -> bool:
        """Check if event has already been processed (idempotency)."""
        # In production, check database
        # For now, use in-memory set
        return event_id in self._processed_events

    async def mark_processed(self, event_id: str) -> None:
        """Mark event as processed."""
        self._processed_events.add(event_id)
        # In production, save to database

    async def handle_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> Dict[str, Any]:
        """
        Handle incoming webhook.

        Args:
            payload: Raw request body
            signature: Webhook signature header

        Returns:
            Processing result
        """
        # Verify signature
        if not await self.verify_signature(payload, signature):
            logger.warning("Invalid webhook signature")
            return {
                "success": False,
                "error": "Invalid signature",
            }

        try:
            import json
            payload_dict = json.loads(payload.decode())
        except Exception as e:
            logger.error(f"Failed to parse webhook payload: {e}")
            return {
                "success": False,
                "error": "Invalid payload",
            }

        # Parse event
        try:
            event = self.parse_event(payload_dict)
        except ValueError as e:
            logger.warning(f"Unknown webhook event: {e}")
            return {
                "success": True,
                "message": "Event type not handled",
            }

        # Check idempotency
        if await self.is_processed(event.event_id):
            logger.info(f"Event {event.event_id} already processed")
            return {
                "success": True,
                "message": "Already processed",
                "event_id": event.event_id,
            }

        # Dispatch to handlers
        handlers = self._handlers.get(event.event_type, [])
        if not handlers:
            logger.info(f"No handlers for event type: {event.event_type}")
            return {
                "success": True,
                "message": "No handlers registered",
                "event_type": event.event_type.value,
            }

        results = []
        for handler in handlers:
            try:
                result = await handler(event, self.db)
                results.append({"handler": handler.__name__, "success": result})
            except Exception as e:
                logger.error(f"Handler {handler.__name__} failed: {e}")
                results.append({
                    "handler": handler.__name__,
                    "success": False,
                    "error": str(e),
                })

        # Mark as processed if at least one handler succeeded
        if any(r.get("success") for r in results):
            await self.mark_processed(event.event_id)

        return {
            "success": True,
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "handlers_called": len(handlers),
            "results": results,
        }


# Default handlers for common events

async def handle_payment_captured(
    event: WebhookEvent, db: Optional[AsyncSession]
) -> bool:
    """Handle payment captured event."""
    logger.info(
        f"Payment captured: {event.payment_id}, "
        f"amount: {event.amount}, "
        f"loan: {event.loan_account_id}"
    )

    if not db:
        return True

    # In production, this would:
    # 1. Find the pending payment record
    # 2. Update payment status to completed
    # 3. Create loan receipt
    # 4. Update loan outstanding
    # 5. Send confirmation notification

    # from app.services.portal.payment_service import PortalPaymentService
    # service = PortalPaymentService(db)
    # await service.process_payment_success(
    #     payment_id=event.payment_id,
    #     gateway_payment_id=event.payment_id,
    #     amount=event.amount,
    #     method=event.method,
    #     loan_account_id=event.loan_account_id,
    # )
    # await db.commit()

    return True


async def handle_payment_failed(
    event: WebhookEvent, db: Optional[AsyncSession]
) -> bool:
    """Handle payment failed event."""
    logger.warning(
        f"Payment failed: {event.payment_id}, "
        f"loan: {event.loan_account_id}"
    )

    if not db:
        return True

    # In production:
    # 1. Update payment record to failed
    # 2. Send failure notification to customer

    return True


async def handle_refund_processed(
    event: WebhookEvent, db: Optional[AsyncSession]
) -> bool:
    """Handle refund processed event."""
    logger.info(
        f"Refund processed: {event.refund_id}, "
        f"payment: {event.payment_id}, "
        f"amount: {event.amount}"
    )

    if not db:
        return True

    # In production:
    # 1. Update refund record
    # 2. Update payment record
    # 3. Adjust loan account if needed

    return True


async def handle_mandate_confirmed(
    event: WebhookEvent, db: Optional[AsyncSession]
) -> bool:
    """Handle NACH/UPI mandate confirmation."""
    logger.info(
        f"Mandate confirmed: {event.payment_id}, "
        f"loan: {event.loan_account_id}"
    )

    if not db:
        return True

    # In production:
    # 1. Update mandate status to active
    # 2. Enable auto-debit for the loan
    # 3. Send confirmation to customer

    return True


async def handle_mandate_rejected(
    event: WebhookEvent, db: Optional[AsyncSession]
) -> bool:
    """Handle mandate rejection."""
    logger.warning(
        f"Mandate rejected: {event.payment_id}, "
        f"loan: {event.loan_account_id}"
    )

    if not db:
        return True

    # In production:
    # 1. Update mandate status to rejected
    # 2. Notify customer to setup again

    return True


# Factory function
def create_webhook_handler(
    gateway: PaymentGateway,
    db: Optional[AsyncSession] = None,
    register_default_handlers: bool = True,
) -> PaymentWebhookHandler:
    """
    Create webhook handler with optional default handlers.

    Args:
        gateway: Payment gateway instance
        db: Database session
        register_default_handlers: Whether to register default handlers

    Returns:
        Configured webhook handler
    """
    handler = PaymentWebhookHandler(gateway, db)

    if register_default_handlers:
        handler.register_handlers({
            WebhookEventType.PAYMENT_CAPTURED: handle_payment_captured,
            WebhookEventType.PAYMENT_FAILED: handle_payment_failed,
            WebhookEventType.REFUND_PROCESSED: handle_refund_processed,
            WebhookEventType.TOKEN_CONFIRMED: handle_mandate_confirmed,
            WebhookEventType.TOKEN_REJECTED: handle_mandate_rejected,
        })

    return handler
