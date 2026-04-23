"""Unified Communication Service.

Provides a unified interface for sending messages across all channels.
Handles provider selection, fallback, logging, and analytics.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.communication.base import (
    CommunicationChannel,
    CommunicationError,
    CommunicationProvider,
    CommunicationRequest,
    CommunicationResult,
    MessagePriority,
    MessageStatus,
    Recipient,
)
from app.integrations.communication.sms import (
    MSG91Provider,
    SMSProvider,
    TextLocalProvider,
    TwilioSMSProvider,
)
from app.integrations.communication.email import (
    AWSSESProvider,
    EmailProvider,
    SendGridProvider,
    SMTPProvider,
)
from app.integrations.communication.push import (
    FirebasePushProvider,
    PushProvider,
)
from app.integrations.communication.whatsapp import (
    WhatsAppBusinessProvider,
    WhatsAppProvider,
)


logger = logging.getLogger(__name__)


# Provider registry
SMS_PROVIDERS: Dict[str, Type[SMSProvider]] = {
    "msg91": MSG91Provider,
    "twilio": TwilioSMSProvider,
    "textlocal": TextLocalProvider,
}

EMAIL_PROVIDERS: Dict[str, Type[EmailProvider]] = {
    "sendgrid": SendGridProvider,
    "aws_ses": AWSSESProvider,
    "smtp": SMTPProvider,
}

PUSH_PROVIDERS: Dict[str, Type[PushProvider]] = {
    "firebase": FirebasePushProvider,
}

WHATSAPP_PROVIDERS: Dict[str, Type[WhatsAppProvider]] = {
    "whatsapp_business": WhatsAppBusinessProvider,
}


class CommunicationService:
    """
    Unified communication service for sending messages across channels.

    Features:
    - Multi-provider support with automatic fallback
    - Template-based messaging
    - Delivery tracking and analytics
    - Rate limiting and throttling
    - Audit logging
    """

    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize communication service.

        Args:
            db: Optional database session for logging
            config: Provider configurations
        """
        self.db = db
        self.config = config or {}
        self._providers: Dict[CommunicationChannel, List[CommunicationProvider]] = {}
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize configured providers."""
        # SMS providers
        sms_config = self.config.get("sms", {})
        if sms_config:
            self._providers[CommunicationChannel.SMS] = []
            for provider_name, provider_config in sms_config.get("providers", {}).items():
                if provider_name in SMS_PROVIDERS and provider_config.get("enabled"):
                    try:
                        provider = SMS_PROVIDERS[provider_name](provider_config)
                        self._providers[CommunicationChannel.SMS].append(provider)
                    except Exception as e:
                        logger.error(f"Failed to initialize SMS provider {provider_name}: {e}")

        # Email providers
        email_config = self.config.get("email", {})
        if email_config:
            self._providers[CommunicationChannel.EMAIL] = []
            for provider_name, provider_config in email_config.get("providers", {}).items():
                if provider_name in EMAIL_PROVIDERS and provider_config.get("enabled"):
                    try:
                        provider = EMAIL_PROVIDERS[provider_name](provider_config)
                        self._providers[CommunicationChannel.EMAIL].append(provider)
                    except Exception as e:
                        logger.error(f"Failed to initialize Email provider {provider_name}: {e}")

        # Push providers
        push_config = self.config.get("push", {})
        if push_config:
            self._providers[CommunicationChannel.PUSH] = []
            for provider_name, provider_config in push_config.get("providers", {}).items():
                if provider_name in PUSH_PROVIDERS and provider_config.get("enabled"):
                    try:
                        provider = PUSH_PROVIDERS[provider_name](provider_config)
                        self._providers[CommunicationChannel.PUSH].append(provider)
                    except Exception as e:
                        logger.error(f"Failed to initialize Push provider {provider_name}: {e}")

        # WhatsApp providers
        whatsapp_config = self.config.get("whatsapp", {})
        if whatsapp_config:
            self._providers[CommunicationChannel.WHATSAPP] = []
            for provider_name, provider_config in whatsapp_config.get("providers", {}).items():
                if provider_name in WHATSAPP_PROVIDERS and provider_config.get("enabled"):
                    try:
                        provider = WHATSAPP_PROVIDERS[provider_name](provider_config)
                        self._providers[CommunicationChannel.WHATSAPP].append(provider)
                    except Exception as e:
                        logger.error(f"Failed to initialize WhatsApp provider {provider_name}: {e}")

    def _get_provider(
        self, channel: CommunicationChannel, preferred: Optional[str] = None
    ) -> Optional[CommunicationProvider]:
        """Get provider for channel with optional preference."""
        providers = self._providers.get(channel, [])
        if not providers:
            return None

        if preferred:
            for provider in providers:
                if provider.provider_name == preferred:
                    return provider

        return providers[0] if providers else None

    async def send(
        self,
        request: CommunicationRequest,
        preferred_provider: Optional[str] = None,
        fallback: bool = True,
    ) -> List[CommunicationResult]:
        """
        Send message through appropriate channel.

        Args:
            request: Communication request
            preferred_provider: Preferred provider name
            fallback: Whether to try other providers on failure

        Returns:
            List of results for each recipient
        """
        channel = request.channel
        providers = self._providers.get(channel, [])

        if not providers:
            raise CommunicationError(
                f"No providers configured for channel: {channel}",
                code="NO_PROVIDER",
            )

        # Reorder providers if preferred
        if preferred_provider:
            providers = sorted(
                providers,
                key=lambda p: 0 if p.provider_name == preferred_provider else 1,
            )

        last_error: Optional[Exception] = None
        results: List[CommunicationResult] = []

        for provider in providers:
            try:
                logger.info(
                    f"Sending {channel} via {provider.provider_name} "
                    f"to {len(request.recipients)} recipients"
                )

                results = await provider.send(request)

                # Check if all succeeded
                all_success = all(r.success for r in results)
                if all_success:
                    await self._log_communication(request, results, provider.provider_name)
                    return results

                # If some failed and fallback enabled, try next provider
                if not fallback:
                    break

                # Get failed recipients for retry
                failed_recipients = [
                    r for r, result in zip(request.recipients, results)
                    if not result.success
                ]

                if failed_recipients:
                    request.recipients = failed_recipients
                    logger.warning(
                        f"{len(failed_recipients)} failed via {provider.provider_name}, "
                        f"trying next provider"
                    )
                else:
                    break

            except CommunicationError as e:
                last_error = e
                logger.error(f"Provider {provider.provider_name} failed: {e}")
                if not fallback:
                    raise
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error with {provider.provider_name}: {e}")
                if not fallback:
                    raise CommunicationError(
                        str(e),
                        code="PROVIDER_ERROR",
                        provider=provider.provider_name,
                    )

        if not results and last_error:
            raise CommunicationError(
                f"All providers failed. Last error: {last_error}",
                code="ALL_PROVIDERS_FAILED",
            )

        await self._log_communication(
            request, results, providers[0].provider_name if providers else None
        )
        return results

    async def send_sms(
        self,
        phone_numbers: List[str],
        message: Optional[str] = None,
        template_id: Optional[str] = None,
        template_params: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        organization_id: Optional[UUID] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
    ) -> List[CommunicationResult]:
        """
        Convenience method to send SMS.

        Args:
            phone_numbers: List of phone numbers
            message: Message content (for non-template)
            template_id: DLT template ID (required in India)
            template_params: Template variables
            priority: Message priority
            organization_id: Organization ID for tracking
            entity_type: Entity type (e.g., "loan_account")
            entity_id: Entity ID for tracking

        Returns:
            List of results
        """
        request = CommunicationRequest(
            channel=CommunicationChannel.SMS,
            recipients=[Recipient(identifier=phone) for phone in phone_numbers],
            content=message,
            template_id=template_id,
            template_params=template_params or {},
            priority=priority,
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return await self.send(request)

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: Optional[str] = None,
        template_id: Optional[str] = None,
        template_params: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        organization_id: Optional[UUID] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
    ) -> List[CommunicationResult]:
        """
        Convenience method to send email.

        Args:
            to_emails: List of email addresses
            subject: Email subject
            body: HTML body content
            template_id: Email template ID
            template_params: Template variables
            attachments: List of attachments
            priority: Message priority
            organization_id: Organization ID for tracking
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            List of results
        """
        from app.integrations.communication.base import Attachment

        attachment_list = []
        if attachments:
            for att in attachments:
                attachment_list.append(
                    Attachment(
                        filename=att["filename"],
                        content=att["content"],
                        content_type=att.get("content_type", "application/octet-stream"),
                        size_bytes=len(att["content"]),
                    )
                )

        request = CommunicationRequest(
            channel=CommunicationChannel.EMAIL,
            recipients=[Recipient(identifier=email) for email in to_emails],
            subject=subject,
            content=body,
            template_id=template_id,
            template_params=template_params or {},
            attachments=attachment_list,
            priority=priority,
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return await self.send(request)

    async def send_push(
        self,
        device_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        organization_id: Optional[UUID] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
    ) -> List[CommunicationResult]:
        """
        Convenience method to send push notification.

        Args:
            device_tokens: List of FCM device tokens
            title: Notification title
            body: Notification body
            data: Custom data payload
            priority: Message priority
            organization_id: Organization ID
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            List of results
        """
        request = CommunicationRequest(
            channel=CommunicationChannel.PUSH,
            recipients=[Recipient(identifier=token) for token in device_tokens],
            subject=title,
            content=body,
            template_params=data or {},
            priority=priority,
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return await self.send(request)

    async def send_whatsapp(
        self,
        phone_numbers: List[str],
        message: Optional[str] = None,
        template_name: Optional[str] = None,
        template_params: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        organization_id: Optional[UUID] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
    ) -> List[CommunicationResult]:
        """
        Convenience method to send WhatsApp message.

        Args:
            phone_numbers: List of phone numbers
            message: Text message (for non-template)
            template_name: WhatsApp template name
            template_params: Template parameters
            priority: Message priority
            organization_id: Organization ID
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            List of results
        """
        request = CommunicationRequest(
            channel=CommunicationChannel.WHATSAPP,
            recipients=[Recipient(identifier=phone) for phone in phone_numbers],
            content=message,
            template_id=template_name,
            template_params=template_params or {},
            priority=priority,
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return await self.send(request)

    async def get_status(
        self, channel: CommunicationChannel, message_id: str
    ) -> CommunicationResult:
        """Get message delivery status."""
        provider = self._get_provider(channel)
        if not provider:
            raise CommunicationError(
                f"No provider for channel: {channel}",
                code="NO_PROVIDER",
            )
        return await provider.get_status(message_id)

    async def get_balance(
        self, channel: CommunicationChannel
    ) -> Dict[str, Any]:
        """Get provider balance/credits."""
        provider = self._get_provider(channel)
        if not provider:
            raise CommunicationError(
                f"No provider for channel: {channel}",
                code="NO_PROVIDER",
            )
        return await provider.get_balance()

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all configured providers."""
        results = {}
        for channel, providers in self._providers.items():
            for provider in providers:
                key = f"{channel.value}:{provider.provider_name}"
                try:
                    results[key] = await provider.health_check()
                except Exception:
                    results[key] = False
        return results

    async def _log_communication(
        self,
        request: CommunicationRequest,
        results: List[CommunicationResult],
        provider_name: Optional[str],
    ) -> None:
        """Log communication for audit trail."""
        if not self.db:
            return

        # TODO: Store in communication_log table
        # This would include:
        # - channel, provider, template_id
        # - organization_id, entity_type, entity_id
        # - recipient count, success count, failure count
        # - timestamp, metadata

        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count

        logger.info(
            f"Communication logged: channel={request.channel}, "
            f"provider={provider_name}, "
            f"recipients={len(results)}, "
            f"success={success_count}, "
            f"failed={failure_count}"
        )


# Factory function for creating service instance
def create_communication_service(
    db: Optional[AsyncSession] = None,
    config: Optional[Dict[str, Any]] = None,
) -> CommunicationService:
    """
    Create communication service with configuration.

    Example config:
    {
        "sms": {
            "providers": {
                "msg91": {
                    "enabled": True,
                    "auth_key": "xxx",
                    "sender_id": "TALNTF"
                }
            }
        },
        "email": {
            "providers": {
                "sendgrid": {
                    "enabled": True,
                    "api_key": "xxx",
                    "from_email": "noreply@company.com"
                }
            }
        },
        "push": {
            "providers": {
                "firebase": {
                    "enabled": True,
                    "server_key": "xxx"
                }
            }
        },
        "whatsapp": {
            "providers": {
                "whatsapp_business": {
                    "enabled": True,
                    "access_token": "xxx",
                    "phone_number_id": "xxx"
                }
            }
        }
    }
    """
    return CommunicationService(db=db, config=config)
