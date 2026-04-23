"""WhatsApp Business API provider implementations."""

import re
from abc import ABC
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.integrations.communication.base import (
    Attachment,
    CommunicationChannel,
    CommunicationError,
    CommunicationProvider,
    CommunicationRequest,
    CommunicationResult,
    MessageStatus,
    Recipient,
)


class WhatsAppProvider(CommunicationProvider, ABC):
    """Base class for WhatsApp providers."""

    channel = CommunicationChannel.WHATSAPP

    def _normalize_phone(self, phone: str, country_code: str = "91") -> str:
        """Normalize phone number for WhatsApp."""
        digits = re.sub(r"\D", "", phone)
        if len(digits) == 10:
            return f"{country_code}{digits}"
        elif len(digits) == 12 and digits.startswith("91"):
            return digits
        return digits

    async def validate_recipient(self, recipient: Recipient) -> bool:
        """Validate WhatsApp number."""
        phone = self._normalize_phone(recipient.identifier)
        # Indian mobile numbers
        pattern = r"^91[6-9]\d{9}$"
        return bool(re.match(pattern, phone))


class WhatsAppBusinessProvider(WhatsAppProvider):
    """WhatsApp Business API provider (Meta Cloud API)."""

    provider_name = "whatsapp_business"

    def _validate_config(self) -> None:
        """Validate WhatsApp Business configuration."""
        required = ["access_token", "phone_number_id"]
        for key in required:
            if key not in self.config:
                raise CommunicationError(
                    f"Missing required config: {key}",
                    code="CONFIG_ERROR",
                    provider=self.provider_name,
                )

    async def send(self, request: CommunicationRequest) -> List[CommunicationResult]:
        """Send WhatsApp message via Business API."""
        results = []
        access_token = self.config["access_token"]
        phone_number_id = self.config["phone_number_id"]
        api_version = self.config.get("api_version", "v18.0")
        base_url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        for recipient in request.recipients:
            to_number = self._normalize_phone(recipient.identifier)

            # Build message payload based on type
            if request.template_id:
                # Template message
                payload = self._build_template_message(
                    to_number, request.template_id, request.template_params
                )
            elif request.attachments:
                # Media message
                payload = await self._build_media_message(
                    to_number, request.content, request.attachments
                )
            else:
                # Text message
                payload = self._build_text_message(to_number, request.content or "")

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        base_url,
                        json=payload,
                        headers=headers,
                        timeout=30.0,
                    )

                    data = response.json()

                    if response.status_code == 200 and "messages" in data:
                        message_info = data["messages"][0]
                        results.append(
                            CommunicationResult(
                                success=True,
                                message_id=message_info.get("id"),
                                provider_message_id=message_info.get("id"),
                                status=MessageStatus.SENT,
                                recipient=recipient.identifier,
                                channel=self.channel,
                                sent_at=datetime.utcnow(),
                                metadata={
                                    "wamid": message_info.get("id"),
                                    "message_status": message_info.get("message_status"),
                                },
                            )
                        )
                    else:
                        error = data.get("error", {})
                        results.append(
                            CommunicationResult(
                                success=False,
                                status=MessageStatus.FAILED,
                                recipient=recipient.identifier,
                                channel=self.channel,
                                error_code=str(error.get("code")),
                                error_message=error.get("message"),
                                metadata=data,
                            )
                        )

            except Exception as e:
                results.append(
                    CommunicationResult(
                        success=False,
                        status=MessageStatus.FAILED,
                        recipient=recipient.identifier,
                        channel=self.channel,
                        error_message=str(e),
                    )
                )

        return results

    def _build_text_message(self, to: str, text: str) -> Dict[str, Any]:
        """Build text message payload."""
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }

    def _build_template_message(
        self, to: str, template_name: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build template message payload."""
        # Build components from params
        components = []

        # Header parameters (if any)
        header_params = params.get("header", [])
        if header_params:
            components.append(
                {
                    "type": "header",
                    "parameters": [
                        {"type": "text", "text": str(p)} for p in header_params
                    ],
                }
            )

        # Body parameters
        body_params = params.get("body", [])
        if body_params:
            components.append(
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(p)} for p in body_params
                    ],
                }
            )

        # Button parameters (if any)
        button_params = params.get("buttons", [])
        for i, button in enumerate(button_params):
            components.append(
                {
                    "type": "button",
                    "sub_type": button.get("sub_type", "url"),
                    "index": str(i),
                    "parameters": [{"type": "text", "text": str(button.get("text", ""))}],
                }
            )

        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": params.get("language", "en")},
                "components": components,
            },
        }

    async def _build_media_message(
        self, to: str, caption: Optional[str], attachments: List[Attachment]
    ) -> Dict[str, Any]:
        """Build media message payload."""
        if not attachments:
            return self._build_text_message(to, caption or "")

        attachment = attachments[0]  # WhatsApp sends one media per message

        # Determine media type
        content_type = attachment.content_type.lower()
        if "image" in content_type:
            media_type = "image"
        elif "video" in content_type:
            media_type = "video"
        elif "audio" in content_type:
            media_type = "audio"
        else:
            media_type = "document"

        # Note: In production, you would upload media first and get media_id
        # For now, we'll use a URL if available
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": media_type,
        }

        media_object: Dict[str, Any] = {}
        if caption:
            media_object["caption"] = caption
        if media_type == "document":
            media_object["filename"] = attachment.filename

        # Would need media_id from upload or link
        # media_object["id"] = media_id  # From upload
        # media_object["link"] = media_url  # Or direct link

        payload[media_type] = media_object
        return payload

    async def get_status(self, message_id: str) -> CommunicationResult:
        """
        Get message status.

        Note: WhatsApp Business API uses webhooks for status updates.
        This method queries the message info if available.
        """
        return CommunicationResult(
            success=True,
            message_id=message_id,
            status=MessageStatus.SENT,
            metadata={
                "note": "Use webhook for real-time status. Status: sent -> delivered -> read"
            },
        )

    async def get_balance(self) -> Dict[str, Any]:
        """Get WhatsApp Business account info."""
        access_token = self.config["access_token"]
        phone_number_id = self.config["phone_number_id"]
        api_version = self.config.get("api_version", "v18.0")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://graph.facebook.com/{api_version}/{phone_number_id}",
                    params={"access_token": access_token},
                    timeout=30.0,
                )

                data = response.json()

                return {
                    "provider": self.provider_name,
                    "phone_number": data.get("display_phone_number"),
                    "verified_name": data.get("verified_name"),
                    "quality_rating": data.get("quality_rating"),
                    "messaging_limit": data.get("messaging_limit_tier"),
                }

        except Exception as e:
            return {
                "provider": self.provider_name,
                "error": str(e),
            }

    async def mark_as_read(self, message_id: str) -> bool:
        """Mark incoming message as read."""
        access_token = self.config["access_token"]
        phone_number_id = self.config["phone_number_id"]
        api_version = self.config.get("api_version", "v18.0")
        base_url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    base_url,
                    json={
                        "messaging_product": "whatsapp",
                        "status": "read",
                        "message_id": message_id,
                    },
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )
                return response.status_code == 200

        except Exception:
            return False

    async def send_interactive_message(
        self,
        to: str,
        header: Optional[str],
        body: str,
        footer: Optional[str],
        buttons: List[Dict[str, str]],
    ) -> CommunicationResult:
        """Send interactive button message."""
        access_token = self.config["access_token"]
        phone_number_id = self.config["phone_number_id"]
        api_version = self.config.get("api_version", "v18.0")
        base_url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"

        to_number = self._normalize_phone(to)

        # Build interactive message
        interactive: Dict[str, Any] = {
            "type": "button",
            "body": {"text": body},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {"id": btn["id"], "title": btn["title"][:20]},
                    }
                    for btn in buttons[:3]  # Max 3 buttons
                ]
            },
        }

        if header:
            interactive["header"] = {"type": "text", "text": header}
        if footer:
            interactive["footer"] = {"text": footer}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "interactive",
            "interactive": interactive,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    base_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )

                data = response.json()

                if response.status_code == 200 and "messages" in data:
                    message_info = data["messages"][0]
                    return CommunicationResult(
                        success=True,
                        message_id=message_info.get("id"),
                        provider_message_id=message_info.get("id"),
                        status=MessageStatus.SENT,
                        recipient=to,
                        channel=self.channel,
                        sent_at=datetime.utcnow(),
                    )
                else:
                    error = data.get("error", {})
                    return CommunicationResult(
                        success=False,
                        status=MessageStatus.FAILED,
                        recipient=to,
                        channel=self.channel,
                        error_code=str(error.get("code")),
                        error_message=error.get("message"),
                    )

        except Exception as e:
            return CommunicationResult(
                success=False,
                status=MessageStatus.FAILED,
                recipient=to,
                channel=self.channel,
                error_message=str(e),
            )

    async def send_list_message(
        self,
        to: str,
        header: Optional[str],
        body: str,
        footer: Optional[str],
        button_text: str,
        sections: List[Dict[str, Any]],
    ) -> CommunicationResult:
        """Send interactive list message."""
        access_token = self.config["access_token"]
        phone_number_id = self.config["phone_number_id"]
        api_version = self.config.get("api_version", "v18.0")
        base_url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"

        to_number = self._normalize_phone(to)

        # Build list interactive message
        interactive: Dict[str, Any] = {
            "type": "list",
            "body": {"text": body},
            "action": {"button": button_text[:20], "sections": sections[:10]},
        }

        if header:
            interactive["header"] = {"type": "text", "text": header}
        if footer:
            interactive["footer"] = {"text": footer}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "interactive",
            "interactive": interactive,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    base_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )

                data = response.json()

                if response.status_code == 200 and "messages" in data:
                    message_info = data["messages"][0]
                    return CommunicationResult(
                        success=True,
                        message_id=message_info.get("id"),
                        provider_message_id=message_info.get("id"),
                        status=MessageStatus.SENT,
                        recipient=to,
                        channel=self.channel,
                        sent_at=datetime.utcnow(),
                    )
                else:
                    error = data.get("error", {})
                    return CommunicationResult(
                        success=False,
                        status=MessageStatus.FAILED,
                        recipient=to,
                        channel=self.channel,
                        error_code=str(error.get("code")),
                        error_message=error.get("message"),
                    )

        except Exception as e:
            return CommunicationResult(
                success=False,
                status=MessageStatus.FAILED,
                recipient=to,
                channel=self.channel,
                error_message=str(e),
            )
