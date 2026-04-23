"""Communication integration services.

Provides unified interfaces for:
- SMS (MSG91, Twilio, TextLocal)
- Email (SendGrid, AWS SES, SMTP)
- Push Notifications (Firebase FCM)
- WhatsApp Business API
"""

from app.integrations.communication.base import (
    CommunicationProvider,
    CommunicationResult,
    CommunicationError,
)
from app.integrations.communication.sms import (
    SMSProvider,
    MSG91Provider,
    TwilioSMSProvider,
    TextLocalProvider,
)
from app.integrations.communication.email import (
    EmailProvider,
    SendGridProvider,
    AWSSESProvider,
    SMTPProvider,
)
from app.integrations.communication.push import (
    PushProvider,
    FirebasePushProvider,
)
from app.integrations.communication.whatsapp import (
    WhatsAppProvider,
    WhatsAppBusinessProvider,
)
from app.integrations.communication.service import CommunicationService

__all__ = [
    # Base
    "CommunicationProvider",
    "CommunicationResult",
    "CommunicationError",
    # SMS
    "SMSProvider",
    "MSG91Provider",
    "TwilioSMSProvider",
    "TextLocalProvider",
    # Email
    "EmailProvider",
    "SendGridProvider",
    "AWSSESProvider",
    "SMTPProvider",
    # Push
    "PushProvider",
    "FirebasePushProvider",
    # WhatsApp
    "WhatsAppProvider",
    "WhatsAppBusinessProvider",
    # Service
    "CommunicationService",
]
