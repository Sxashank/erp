"""Payment Gateway Integration.

Provides integration with payment gateways for online payments.
Supports: Razorpay, PayU, CCAvenue
"""

from app.integrations.payment_gateway.base import (
    PaymentGateway,
    PaymentOrder,
    PaymentResult,
    RefundResult,
    PaymentStatus,
    RefundStatus,
    GatewayError,
)
from app.integrations.payment_gateway.razorpay import RazorpayGateway
from app.integrations.payment_gateway.webhook_handler import (
    PaymentWebhookHandler,
    WebhookEventType,
    WebhookEvent,
    create_webhook_handler,
)

__all__ = [
    "PaymentGateway",
    "PaymentOrder",
    "PaymentResult",
    "RefundResult",
    "PaymentStatus",
    "RefundStatus",
    "GatewayError",
    "RazorpayGateway",
    "PaymentWebhookHandler",
    "WebhookEventType",
    "WebhookEvent",
    "create_webhook_handler",
]
