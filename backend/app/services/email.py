"""Email service for sending emails via SMTP."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""

    def __init__(self):
        """Initialize email service."""
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
        self.use_tls = settings.SMTP_USE_TLS
        self.enabled = settings.SMTP_ENABLED

    async def send_email(
        self,
        to: List[str],
        subject: str,
        html_body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            html_body: HTML content of the email
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients
            reply_to: Optional reply-to address

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(
                f"Email sending disabled. Would have sent to {to}: {subject}"
            )
            return True

        if not to:
            logger.warning("No recipients specified for email")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = ", ".join(to)

            if cc:
                msg["Cc"] = ", ".join(cc)

            if reply_to:
                msg["Reply-To"] = reply_to

            # Attach HTML content
            html_part = MIMEText(html_body, "html")
            msg.attach(html_part)

            # Build recipient list
            all_recipients = list(to)
            if cc:
                all_recipients.extend(cc)
            if bcc:
                all_recipients.extend(bcc)

            # Send email
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()

                if self.user and self.password:
                    server.login(self.user, self.password)

                server.sendmail(self.from_email, all_recipients, msg.as_string())

            logger.info(f"Email sent successfully to {to}: {subject}")
            return True

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    async def send_template_email(
        self,
        to: List[str],
        subject_template: str,
        body_template: str,
        context: dict,
        cc: Optional[List[str]] = None,
    ) -> bool:
        """
        Send an email using templates with variable substitution.

        Args:
            to: List of recipient email addresses
            subject_template: Subject with {placeholders}
            body_template: HTML body with {placeholders}
            context: Dictionary of values to substitute
            cc: Optional list of CC recipients

        Returns:
            True if email was sent successfully
        """
        try:
            # Replace placeholders in subject and body
            subject = self._render_template(subject_template, context)
            html_body = self._render_template(body_template, context)

            return await self.send_email(
                to=to,
                subject=subject,
                html_body=html_body,
                cc=cc,
            )
        except Exception as e:
            logger.error(f"Error rendering email template: {e}")
            return False

    def _render_template(self, template: str, context: dict) -> str:
        """
        Render a template string with context variables.

        Uses simple {placeholder} substitution.
        """
        result = template
        for key, value in context.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value) if value is not None else "")
        return result


# Singleton instance
email_service = EmailService()
