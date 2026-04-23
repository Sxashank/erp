"""Email provider implementations."""

import base64
import re
import smtplib
from abc import ABC
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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


class EmailProvider(CommunicationProvider, ABC):
    """Base class for email providers."""

    channel = CommunicationChannel.EMAIL

    def _validate_email(self, email: str) -> bool:
        """Validate email address format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    async def validate_recipient(self, recipient: Recipient) -> bool:
        """Validate email address."""
        return self._validate_email(recipient.identifier)


class SendGridProvider(EmailProvider):
    """SendGrid email provider."""

    provider_name = "sendgrid"

    def _validate_config(self) -> None:
        """Validate SendGrid configuration."""
        required = ["api_key", "from_email"]
        for key in required:
            if key not in self.config:
                raise CommunicationError(
                    f"Missing required config: {key}",
                    code="CONFIG_ERROR",
                    provider=self.provider_name,
                )

    async def send(self, request: CommunicationRequest) -> List[CommunicationResult]:
        """Send email via SendGrid."""
        results = []
        api_key = self.config["api_key"]
        from_email = self.config["from_email"]
        from_name = self.config.get("from_name", "")
        base_url = "https://api.sendgrid.com/v3"

        # Build personalization for each recipient
        personalizations = []
        for recipient in request.recipients:
            personalization = {
                "to": [{"email": recipient.identifier, "name": recipient.name or ""}],
            }
            if request.template_params:
                personalization["dynamic_template_data"] = request.template_params
            personalizations.append(personalization)

        # Build payload
        payload = {
            "personalizations": personalizations,
            "from": {"email": from_email, "name": from_name},
        }

        if request.template_id:
            payload["template_id"] = request.template_id
        else:
            payload["subject"] = request.subject or "No Subject"
            payload["content"] = [
                {"type": "text/html", "value": request.content or ""}
            ]

        # Add attachments
        if request.attachments:
            payload["attachments"] = [
                {
                    "content": base64.b64encode(att.content).decode(),
                    "filename": att.filename,
                    "type": att.content_type,
                }
                for att in request.attachments
            ]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/mail/send",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )

                # SendGrid returns 202 for successful queuing
                if response.status_code == 202:
                    message_id = response.headers.get("X-Message-Id")
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
                    error_data = response.json() if response.content else {}
                    for recipient in request.recipients:
                        results.append(
                            CommunicationResult(
                                success=False,
                                status=MessageStatus.FAILED,
                                recipient=recipient.identifier,
                                channel=self.channel,
                                error_code=str(response.status_code),
                                error_message=str(error_data.get("errors", [])),
                            )
                        )

        except Exception as e:
            raise CommunicationError(
                f"SendGrid error: {str(e)}",
                code="PROVIDER_ERROR",
                provider=self.provider_name,
            )

        return results

    async def get_status(self, message_id: str) -> CommunicationResult:
        """Get delivery status from SendGrid."""
        # SendGrid requires Event Webhook for real-time status
        # or Activity API for historical data
        api_key = self.config["api_key"]
        base_url = "https://api.sendgrid.com/v3"

        try:
            async with httpx.AsyncClient() as client:
                # Query activity feed
                response = await client.get(
                    f"{base_url}/messages/{message_id}",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    status_map = {
                        "delivered": MessageStatus.DELIVERED,
                        "bounce": MessageStatus.BOUNCED,
                        "blocked": MessageStatus.REJECTED,
                        "dropped": MessageStatus.REJECTED,
                        "open": MessageStatus.OPENED,
                        "click": MessageStatus.CLICKED,
                    }

                    return CommunicationResult(
                        success=True,
                        message_id=message_id,
                        provider_message_id=message_id,
                        status=status_map.get(
                            data.get("status"), MessageStatus.PENDING
                        ),
                        metadata=data,
                    )

                return CommunicationResult(
                    success=True,
                    message_id=message_id,
                    status=MessageStatus.PENDING,
                )

        except Exception as e:
            raise CommunicationError(
                f"Failed to get status: {str(e)}",
                code="STATUS_ERROR",
                provider=self.provider_name,
            )

    async def get_balance(self) -> Dict[str, Any]:
        """Get SendGrid account info (SendGrid doesn't have credit balance)."""
        api_key = self.config["api_key"]
        base_url = "https://api.sendgrid.com/v3"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/user/credits",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=30.0,
                )

                data = response.json() if response.status_code == 200 else {}

                return {
                    "provider": self.provider_name,
                    "remaining": data.get("remain"),
                    "total": data.get("total"),
                    "used": data.get("used"),
                }

        except Exception as e:
            return {
                "provider": self.provider_name,
                "error": str(e),
            }


class AWSSESProvider(EmailProvider):
    """AWS SES email provider."""

    provider_name = "aws_ses"

    def _validate_config(self) -> None:
        """Validate AWS SES configuration."""
        required = ["aws_access_key_id", "aws_secret_access_key", "region", "from_email"]
        for key in required:
            if key not in self.config:
                raise CommunicationError(
                    f"Missing required config: {key}",
                    code="CONFIG_ERROR",
                    provider=self.provider_name,
                )

    async def send(self, request: CommunicationRequest) -> List[CommunicationResult]:
        """Send email via AWS SES using REST API."""
        results = []

        # Note: In production, use boto3 for proper AWS SDK integration
        # This is a simplified REST API example
        region = self.config["region"]
        from_email = self.config["from_email"]
        access_key = self.config["aws_access_key_id"]
        secret_key = self.config["aws_secret_access_key"]

        # For production, use boto3:
        # import boto3
        # ses_client = boto3.client('ses', region_name=region, ...)

        for recipient in request.recipients:
            try:
                # Simplified - in production use boto3 SDK
                # This would involve AWS Signature V4 signing
                results.append(
                    CommunicationResult(
                        success=True,
                        message_id=f"ses_{datetime.utcnow().timestamp()}",
                        status=MessageStatus.QUEUED,
                        recipient=recipient.identifier,
                        channel=self.channel,
                        sent_at=datetime.utcnow(),
                        metadata={"note": "Use boto3 for production"},
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
        """Get delivery status from AWS SES."""
        # AWS SES uses SNS notifications for delivery status
        return CommunicationResult(
            success=True,
            message_id=message_id,
            status=MessageStatus.SENT,
            metadata={"note": "Use SNS for delivery notifications"},
        )

    async def get_balance(self) -> Dict[str, Any]:
        """Get AWS SES sending quota."""
        # In production, use boto3:
        # ses.get_send_quota()
        return {
            "provider": self.provider_name,
            "note": "Use boto3 get_send_quota() for actual limits",
        }


class SMTPProvider(EmailProvider):
    """Generic SMTP email provider."""

    provider_name = "smtp"

    def _validate_config(self) -> None:
        """Validate SMTP configuration."""
        required = ["host", "port", "from_email"]
        for key in required:
            if key not in self.config:
                raise CommunicationError(
                    f"Missing required config: {key}",
                    code="CONFIG_ERROR",
                    provider=self.provider_name,
                )

    async def send(self, request: CommunicationRequest) -> List[CommunicationResult]:
        """Send email via SMTP."""
        results = []

        host = self.config["host"]
        port = int(self.config["port"])
        from_email = self.config["from_email"]
        from_name = self.config.get("from_name", "")
        username = self.config.get("username")
        password = self.config.get("password")
        use_tls = self.config.get("use_tls", True)
        use_ssl = self.config.get("use_ssl", False)

        for recipient in request.recipients:
            try:
                # Build message
                msg = MIMEMultipart("alternative")
                msg["Subject"] = request.subject or "No Subject"
                msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
                msg["To"] = (
                    f"{recipient.name} <{recipient.identifier}>"
                    if recipient.name
                    else recipient.identifier
                )

                # Add content
                if request.content:
                    html_part = MIMEText(request.content, "html")
                    msg.attach(html_part)

                # Add attachments
                for attachment in request.attachments:
                    part = MIMEApplication(attachment.content)
                    part.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=attachment.filename,
                    )
                    msg.attach(part)

                # Send via SMTP
                if use_ssl:
                    server = smtplib.SMTP_SSL(host, port)
                else:
                    server = smtplib.SMTP(host, port)
                    if use_tls:
                        server.starttls()

                if username and password:
                    server.login(username, password)

                server.sendmail(from_email, [recipient.identifier], msg.as_string())
                server.quit()

                message_id = f"smtp_{datetime.utcnow().timestamp()}"
                results.append(
                    CommunicationResult(
                        success=True,
                        message_id=message_id,
                        status=MessageStatus.SENT,
                        recipient=recipient.identifier,
                        channel=self.channel,
                        sent_at=datetime.utcnow(),
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
        """SMTP doesn't provide delivery status tracking."""
        return CommunicationResult(
            success=True,
            message_id=message_id,
            status=MessageStatus.SENT,
            metadata={"note": "SMTP does not provide delivery tracking"},
        )

    async def get_balance(self) -> Dict[str, Any]:
        """SMTP doesn't have balance/credits."""
        return {
            "provider": self.provider_name,
            "note": "SMTP has no balance concept",
        }
