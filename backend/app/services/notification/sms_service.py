"""SMS service for sending SMS notifications."""

import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    """Service for sending SMS messages."""

    def __init__(self):
        """Initialize SMS service."""
        self.enabled = getattr(settings, 'SMS_ENABLED', False)
        self.provider = getattr(settings, 'SMS_PROVIDER', 'twilio')
        self.api_key = getattr(settings, 'SMS_API_KEY', '')
        self.api_secret = getattr(settings, 'SMS_API_SECRET', '')
        self.sender_id = getattr(settings, 'SMS_SENDER_ID', 'NBFCERP')

    async def send_sms(
        self,
        to: str,
        message: str,
        sender_id: Optional[str] = None,
    ) -> bool:
        """
        Send an SMS message.

        Args:
            to: Recipient phone number (with country code)
            message: SMS message content
            sender_id: Optional sender ID override

        Returns:
            True if SMS was sent successfully
        """
        if not self.enabled:
            logger.info(
                f"SMS sending disabled. Would have sent to {to}: {message[:50]}..."
            )
            return True

        if not to:
            logger.warning("No phone number specified for SMS")
            return False

        # Normalize phone number
        phone = self._normalize_phone(to)

        try:
            # Route to appropriate provider
            if self.provider == 'twilio':
                return await self._send_via_twilio(phone, message, sender_id)
            elif self.provider == 'msg91':
                return await self._send_via_msg91(phone, message, sender_id)
            elif self.provider == 'textlocal':
                return await self._send_via_textlocal(phone, message, sender_id)
            else:
                logger.error(f"Unknown SMS provider: {self.provider}")
                return False

        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False

    async def _send_via_twilio(
        self,
        to: str,
        message: str,
        sender_id: Optional[str],
    ) -> bool:
        """Send SMS via Twilio."""
        try:
            # Twilio integration
            # In production, use twilio-python SDK:
            # from twilio.rest import Client
            # client = Client(self.api_key, self.api_secret)
            # client.messages.create(
            #     to=to,
            #     from_=sender_id or self.sender_id,
            #     body=message,
            # )
            logger.info(f"Twilio SMS to {to}: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Twilio SMS error: {e}")
            return False

    async def _send_via_msg91(
        self,
        to: str,
        message: str,
        sender_id: Optional[str],
    ) -> bool:
        """Send SMS via MSG91 (India)."""
        try:
            import httpx

            url = "https://api.msg91.com/api/v5/flow/"
            headers = {
                "authkey": self.api_key,
                "Content-Type": "application/json",
            }
            payload = {
                "sender": sender_id or self.sender_id,
                "route": "4",  # Transactional route
                "country": "91",
                "sms": [{"message": message, "to": [to]}],
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info(f"MSG91 SMS to {to}: {message[:50]}...")
                return True

        except Exception as e:
            logger.error(f"MSG91 SMS error: {e}")
            return False

    async def _send_via_textlocal(
        self,
        to: str,
        message: str,
        sender_id: Optional[str],
    ) -> bool:
        """Send SMS via TextLocal (India/UK)."""
        try:
            import httpx

            url = "https://api.textlocal.in/send/"
            payload = {
                "apikey": self.api_key,
                "numbers": to,
                "message": message,
                "sender": sender_id or self.sender_id,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=payload)
                response.raise_for_status()
                data = response.json()
                if data.get("status") == "success":
                    logger.info(f"TextLocal SMS to {to}: {message[:50]}...")
                    return True
                else:
                    logger.error(f"TextLocal SMS failed: {data}")
                    return False

        except Exception as e:
            logger.error(f"TextLocal SMS error: {e}")
            return False

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number format."""
        # Remove spaces, dashes, and parentheses
        phone = "".join(c for c in phone if c.isdigit() or c == "+")

        # Add country code if missing (default to India +91)
        if not phone.startswith("+"):
            if phone.startswith("0"):
                phone = phone[1:]
            phone = "+91" + phone

        return phone

    async def send_otp(
        self,
        to: str,
        otp: str,
        template_id: Optional[str] = None,
    ) -> bool:
        """
        Send OTP via SMS.

        Args:
            to: Recipient phone number
            otp: OTP code
            template_id: Optional DLT template ID for India

        Returns:
            True if OTP SMS was sent successfully
        """
        message = f"Your OTP is {otp}. Valid for 10 minutes. Do not share with anyone."
        return await self.send_sms(to, message)

    async def send_bulk_sms(
        self,
        recipients: list[str],
        message: str,
        sender_id: Optional[str] = None,
    ) -> dict:
        """
        Send bulk SMS to multiple recipients.

        Args:
            recipients: List of phone numbers
            message: SMS message content
            sender_id: Optional sender ID

        Returns:
            Dict with success/failed counts
        """
        results = {"success": 0, "failed": 0, "errors": []}

        for recipient in recipients:
            try:
                success = await self.send_sms(recipient, message, sender_id)
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"phone": recipient, "error": str(e)})

        return results


# Singleton instance
sms_service = SMSService()
