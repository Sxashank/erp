"""External integrations for the ERP system.

This package contains integrations with:
- Communication providers (SMS, Email, Push, WhatsApp)
- Payment gateways (Razorpay, NACH)
- eSign providers (Aadhaar eSign)
- Government APIs (CERSAI)
"""

# Communication
from app.integrations.communication import (
    CommunicationService,
    CommunicationProvider,
    CommunicationResult,
    CommunicationError,
    MSG91Provider,
    TwilioSMSProvider,
    SendGridProvider,
    FirebasePushProvider,
    WhatsAppBusinessProvider,
)

# Payment Gateway
from app.integrations.payment_gateway import (
    PaymentGateway,
    PaymentOrder,
    PaymentResult,
    PaymentStatus,
    RazorpayGateway,
    PaymentWebhookHandler,
    create_webhook_handler,
)

# eSign
from app.integrations.esign import (
    ESignService,
    ESignProvider,
    ESignRequest,
    ESignResponse,
    ESignStatus,
    AadhaarESignProvider,
)

# CERSAI
from app.integrations.cersai import (
    CersaiClient,
    CersaiError,
    RegistrationRequest,
    RegistrationResponse,
    RegistrationStatus,
    SearchRequest,
    SearchResponse,
    TransactionType,
    AssetType,
)

__all__ = [
    # Communication
    "CommunicationService",
    "CommunicationProvider",
    "CommunicationResult",
    "CommunicationError",
    "MSG91Provider",
    "TwilioSMSProvider",
    "SendGridProvider",
    "FirebasePushProvider",
    "WhatsAppBusinessProvider",
    # Payment Gateway
    "PaymentGateway",
    "PaymentOrder",
    "PaymentResult",
    "PaymentStatus",
    "RazorpayGateway",
    "PaymentWebhookHandler",
    "create_webhook_handler",
    # eSign
    "ESignService",
    "ESignProvider",
    "ESignRequest",
    "ESignResponse",
    "ESignStatus",
    "AadhaarESignProvider",
    # CERSAI
    "CersaiClient",
    "CersaiError",
    "RegistrationRequest",
    "RegistrationResponse",
    "RegistrationStatus",
    "SearchRequest",
    "SearchResponse",
    "TransactionType",
    "AssetType",
]
