"""SMS provider implementations."""

import re
from abc import ABC
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.integrations.communication.base import (
    CommunicationChannel,
    CommunicationError,
    CommunicationProvider,
    CommunicationRequest,
    CommunicationResult,
    MessageStatus,
    Recipient,
)


class SMSProvider(CommunicationProvider, ABC):
    """Base class for SMS providers."""

    channel = CommunicationChannel.SMS

    def _normalize_phone(self, phone: str, country_code: str = "91") -> str:
        """Normalize phone number to E.164 format."""
        # Remove all non-digit characters
        digits = re.sub(r"\D", "", phone)

        # Handle Indian numbers
        if len(digits) == 10:
            return f"{country_code}{digits}"
        elif len(digits) == 12 and digits.startswith("91"):
            return digits
        elif len(digits) == 11 and digits.startswith("0"):
            return f"{country_code}{digits[1:]}"

        return digits

    async def validate_recipient(self, recipient: Recipient) -> bool:
        """Validate phone number."""
        phone = self._normalize_phone(recipient.identifier)
        # Indian mobile numbers: 10 digits starting with 6-9
        pattern = r"^91[6-9]\d{9}$"
        return bool(re.match(pattern, phone))


class MSG91Provider(SMSProvider):
    """MSG91 SMS provider (popular in India)."""

    provider_name = "msg91"

    def _validate_config(self) -> None:
        """Validate MSG91 configuration."""
        required = ["auth_key", "sender_id"]
        for key in required:
            if key not in self.config:
                raise CommunicationError(
                    f"Missing required config: {key}",
                    code="CONFIG_ERROR",
                    provider=self.provider_name,
                )

    async def send(self, request: CommunicationRequest) -> List[CommunicationResult]:
        """Send SMS via MSG91."""
        results = []
        auth_key = self.config["auth_key"]
        sender_id = self.config["sender_id"]
        base_url = self.config.get("base_url", "https://control.msg91.com/api/v5")

        # Prepare recipients
        mobiles = []
        for recipient in request.recipients:
            phone = self._normalize_phone(recipient.identifier)
            mobiles.append({"mobiles": phone, **request.template_params})

        # Build payload
        payload = {
            "sender": sender_id,
            "route": self.config.get("route", "4"),  # Transactional
            "country": self.config.get("country", "91"),
        }

        if request.template_id:
            # DLT template-based SMS
            payload["template_id"] = request.template_id
            payload["recipients"] = mobiles
        else:
            # Plain text SMS
            payload["message"] = request.content
            payload["mobiles"] = ",".join(
                [self._normalize_phone(r.identifier) for r in request.recipients]
            )

        headers = {
            "authkey": auth_key,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                if request.template_id:
                    response = await client.post(
                        f"{base_url}/flow/",
                        json=payload,
                        headers=headers,
                        timeout=30.0,
                    )
                else:
                    response = await client.post(
                        f"{base_url}/sendhttp.php",
                        json=payload,
                        headers=headers,
                        timeout=30.0,
                    )

                response_data = response.json()

                if response.status_code == 200 and response_data.get("type") == "success":
                    message_id = response_data.get("request_id")
                    for recipient in request.recipients:
                        results.append(
                            CommunicationResult(
                                success=True,
                                message_id=message_id,
                                provider_message_id=message_id,
                                status=MessageStatus.QUEUED,
                                recipient=recipient.identifier,
                                channel=self.channel,
                                sent_at=datetime.utcnow(),
                            )
                        )
                else:
                    error_msg = response_data.get("message", "Unknown error")
                    for recipient in request.recipients:
                        results.append(
                            CommunicationResult(
                                success=False,
                                status=MessageStatus.FAILED,
                                recipient=recipient.identifier,
                                channel=self.channel,
                                error_code=str(response.status_code),
                                error_message=error_msg,
                            )
                        )

        except httpx.TimeoutException:
            raise CommunicationError(
                "MSG91 request timeout",
                code="TIMEOUT",
                provider=self.provider_name,
            )
        except Exception as e:
            raise CommunicationError(
                f"MSG91 error: {str(e)}",
                code="PROVIDER_ERROR",
                provider=self.provider_name,
            )

        return results

    async def get_status(self, message_id: str) -> CommunicationResult:
        """Get delivery status from MSG91."""
        auth_key = self.config["auth_key"]
        base_url = self.config.get("base_url", "https://control.msg91.com/api/v5")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/report.php",
                    params={"request_id": message_id},
                    headers={"authkey": auth_key},
                    timeout=30.0,
                )

                data = response.json()

                status_map = {
                    "1": MessageStatus.DELIVERED,
                    "2": MessageStatus.FAILED,
                    "3": MessageStatus.SENT,
                    "17": MessageStatus.REJECTED,
                    "26": MessageStatus.PENDING,
                }

                return CommunicationResult(
                    success=True,
                    message_id=message_id,
                    provider_message_id=message_id,
                    status=status_map.get(str(data.get("status")), MessageStatus.PENDING),
                    metadata=data,
                )

        except Exception as e:
            raise CommunicationError(
                f"Failed to get status: {str(e)}",
                code="STATUS_ERROR",
                provider=self.provider_name,
            )

    async def get_balance(self) -> Dict[str, Any]:
        """Get MSG91 account balance."""
        auth_key = self.config["auth_key"]
        base_url = self.config.get("base_url", "https://control.msg91.com/api")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/balance.php",
                    params={"authkey": auth_key, "type": "4"},
                    timeout=30.0,
                )

                return {
                    "provider": self.provider_name,
                    "balance": response.text,
                    "credits": int(response.text) if response.text.isdigit() else 0,
                }

        except Exception as e:
            raise CommunicationError(
                f"Failed to get balance: {str(e)}",
                code="BALANCE_ERROR",
                provider=self.provider_name,
            )


class TwilioSMSProvider(SMSProvider):
    """Twilio SMS provider."""

    provider_name = "twilio"

    def _validate_config(self) -> None:
        """Validate Twilio configuration."""
        required = ["account_sid", "auth_token", "from_number"]
        for key in required:
            if key not in self.config:
                raise CommunicationError(
                    f"Missing required config: {key}",
                    code="CONFIG_ERROR",
                    provider=self.provider_name,
                )

    async def send(self, request: CommunicationRequest) -> List[CommunicationResult]:
        """Send SMS via Twilio."""
        results = []
        account_sid = self.config["account_sid"]
        auth_token = self.config["auth_token"]
        from_number = self.config["from_number"]
        base_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}"

        for recipient in request.recipients:
            to_number = f"+{self._normalize_phone(recipient.identifier)}"

            # Use template or content
            body = request.content
            if request.template_id and request.template_params:
                # Twilio ContentSid for templates
                pass  # Would use messaging service with content template

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{base_url}/Messages.json",
                        auth=(account_sid, auth_token),
                        data={
                            "To": to_number,
                            "From": from_number,
                            "Body": body,
                        },
                        timeout=30.0,
                    )

                    data = response.json()

                    if response.status_code in [200, 201]:
                        results.append(
                            CommunicationResult(
                                success=True,
                                message_id=data.get("sid"),
                                provider_message_id=data.get("sid"),
                                status=MessageStatus.QUEUED,
                                recipient=recipient.identifier,
                                channel=self.channel,
                                cost=float(data.get("price", 0)) if data.get("price") else None,
                                sent_at=datetime.utcnow(),
                            )
                        )
                    else:
                        results.append(
                            CommunicationResult(
                                success=False,
                                status=MessageStatus.FAILED,
                                recipient=recipient.identifier,
                                channel=self.channel,
                                error_code=str(data.get("code")),
                                error_message=data.get("message"),
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

    async def get_status(self, message_id: str) -> CommunicationResult:
        """Get delivery status from Twilio."""
        account_sid = self.config["account_sid"]
        auth_token = self.config["auth_token"]
        base_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/Messages/{message_id}.json",
                    auth=(account_sid, auth_token),
                    timeout=30.0,
                )

                data = response.json()

                status_map = {
                    "queued": MessageStatus.QUEUED,
                    "sending": MessageStatus.PENDING,
                    "sent": MessageStatus.SENT,
                    "delivered": MessageStatus.DELIVERED,
                    "failed": MessageStatus.FAILED,
                    "undelivered": MessageStatus.FAILED,
                }

                return CommunicationResult(
                    success=True,
                    message_id=message_id,
                    provider_message_id=message_id,
                    status=status_map.get(data.get("status"), MessageStatus.PENDING),
                    cost=float(data.get("price", 0)) if data.get("price") else None,
                    metadata=data,
                )

        except Exception as e:
            raise CommunicationError(
                f"Failed to get status: {str(e)}",
                code="STATUS_ERROR",
                provider=self.provider_name,
            )

    async def get_balance(self) -> Dict[str, Any]:
        """Get Twilio account balance."""
        account_sid = self.config["account_sid"]
        auth_token = self.config["auth_token"]
        base_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/Balance.json",
                    auth=(account_sid, auth_token),
                    timeout=30.0,
                )

                data = response.json()

                return {
                    "provider": self.provider_name,
                    "balance": data.get("balance"),
                    "currency": data.get("currency"),
                }

        except Exception as e:
            raise CommunicationError(
                f"Failed to get balance: {str(e)}",
                code="BALANCE_ERROR",
                provider=self.provider_name,
            )


class TextLocalProvider(SMSProvider):
    """TextLocal SMS provider (popular in India)."""

    provider_name = "textlocal"

    def _validate_config(self) -> None:
        """Validate TextLocal configuration."""
        required = ["api_key", "sender"]
        for key in required:
            if key not in self.config:
                raise CommunicationError(
                    f"Missing required config: {key}",
                    code="CONFIG_ERROR",
                    provider=self.provider_name,
                )

    async def send(self, request: CommunicationRequest) -> List[CommunicationResult]:
        """Send SMS via TextLocal."""
        results = []
        api_key = self.config["api_key"]
        sender = self.config["sender"]
        base_url = self.config.get("base_url", "https://api.textlocal.in")

        numbers = ",".join(
            [self._normalize_phone(r.identifier) for r in request.recipients]
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/send/",
                    data={
                        "apikey": api_key,
                        "numbers": numbers,
                        "message": request.content,
                        "sender": sender,
                    },
                    timeout=30.0,
                )

                data = response.json()

                if data.get("status") == "success":
                    for msg in data.get("messages", []):
                        results.append(
                            CommunicationResult(
                                success=True,
                                message_id=msg.get("id"),
                                provider_message_id=msg.get("id"),
                                status=MessageStatus.QUEUED,
                                recipient=msg.get("recipient"),
                                channel=self.channel,
                                credits_used=data.get("balance"),
                                sent_at=datetime.utcnow(),
                            )
                        )
                else:
                    for error in data.get("errors", [{"message": "Unknown error"}]):
                        for recipient in request.recipients:
                            results.append(
                                CommunicationResult(
                                    success=False,
                                    status=MessageStatus.FAILED,
                                    recipient=recipient.identifier,
                                    channel=self.channel,
                                    error_code=str(error.get("code")),
                                    error_message=error.get("message"),
                                )
                            )

        except Exception as e:
            raise CommunicationError(
                f"TextLocal error: {str(e)}",
                code="PROVIDER_ERROR",
                provider=self.provider_name,
            )

        return results

    async def get_status(self, message_id: str) -> CommunicationResult:
        """Get delivery status from TextLocal."""
        api_key = self.config["api_key"]
        base_url = self.config.get("base_url", "https://api.textlocal.in")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/status/",
                    data={"apikey": api_key, "message_id": message_id},
                    timeout=30.0,
                )

                data = response.json()

                status_map = {
                    "D": MessageStatus.DELIVERED,
                    "U": MessageStatus.FAILED,
                    "I": MessageStatus.REJECTED,
                    "P": MessageStatus.PENDING,
                }

                message_data = data.get("message", {})
                return CommunicationResult(
                    success=True,
                    message_id=message_id,
                    provider_message_id=message_id,
                    status=status_map.get(
                        message_data.get("status"), MessageStatus.PENDING
                    ),
                    metadata=data,
                )

        except Exception as e:
            raise CommunicationError(
                f"Failed to get status: {str(e)}",
                code="STATUS_ERROR",
                provider=self.provider_name,
            )

    async def get_balance(self) -> Dict[str, Any]:
        """Get TextLocal account balance."""
        api_key = self.config["api_key"]
        base_url = self.config.get("base_url", "https://api.textlocal.in")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/balance/",
                    data={"apikey": api_key},
                    timeout=30.0,
                )

                data = response.json()

                return {
                    "provider": self.provider_name,
                    "balance": data.get("balance", {}).get("sms"),
                    "credits": data.get("balance", {}).get("sms"),
                }

        except Exception as e:
            raise CommunicationError(
                f"Failed to get balance: {str(e)}",
                code="BALANCE_ERROR",
                provider=self.provider_name,
            )
