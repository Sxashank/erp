"""Unified communication surface (STAGE-6-PENDING-communication-service closure).

A single API for sms / email / push dispatch so callers (workers,
workflow-engine notifications, portal OTP) don't have to know which
channel backs a given template. The underlying providers are gated by
feature flags (`sms_live`, `email_live`, `push_live`); when a provider
flag is `MOCK` or `OFF`, this service returns a deterministic stub
result so tests and non-prod envs exercise the same code path.

See CLAUDE.md §4.17, §6.7 and STAGE-6-PENDING-{sms,email,push}-live.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog

from app.core.feature_flags import FeatureFlagState, get_flag
from app.services.email import email_service
from app.services.notification.push_service import push_service
from app.services.notification.sms_service import sms_service

logger = structlog.get_logger("communication")


class Channel(str, Enum):
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"


class DispatchStatus(str, Enum):
    SENT = "sent"  # provider acknowledged
    QUEUED = "queued"  # accepted for async send (bulk fan-out)
    MOCKED = "mocked"  # running in dev/test — logged but not sent
    DISABLED = "disabled"  # feature flag OFF — no attempt made
    FAILED = "failed"  # transport error; check result.error


@dataclass(frozen=True)
class DispatchResult:
    channel: Channel
    status: DispatchStatus
    provider_message_id: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class Recipient:
    user_id: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    device_token: str | None = None

    def target_for(self, channel: Channel) -> str | None:
        if channel is Channel.EMAIL:
            return self.email
        if channel is Channel.SMS:
            return self.phone
        if channel is Channel.PUSH:
            return self.device_token
        if channel is Channel.IN_APP:
            return self.user_id
        return None


_CHANNEL_FLAG: dict[Channel, str] = {
    Channel.SMS: "sms_live",
    Channel.EMAIL: "email_live",
    Channel.PUSH: "push_live",
    Channel.IN_APP: "otel_export",  # in-app is always on; gated by a dummy flag here
}


class CommunicationService:
    """Single entry point for outbound notifications.

    Concrete provider clients (Msg91, SES, FCM, …) register against this
    service via `register_provider()`. Until those clients land
    (STAGE-6-PENDING-{sms,email,push}-live), dispatch falls through to
    structured-log MOCK behaviour.
    """

    def __init__(self) -> None:
        self._providers: dict[Channel, Any] = {}

    def register_provider(self, channel: Channel, provider: Any) -> None:
        """Install a real provider client for a channel.

        Provider must expose `async send(recipient, template_code, context)
        -> DispatchResult`."""
        self._providers[channel] = provider

    async def send(
        self,
        *,
        channel: Channel,
        recipient: Recipient,
        template_code: str,
        context: dict[str, Any] | None = None,
    ) -> DispatchResult:
        """Dispatch one notification and return the outcome."""
        flag = _CHANNEL_FLAG.get(channel)
        state = get_flag(flag) if flag else FeatureFlagState.MOCK

        target = recipient.target_for(channel)
        if not target:
            logger.info(
                "communication_dispatch_no_target",
                channel=channel,
                template_code=template_code,
                recipient_user_id=recipient.user_id,
            )
            return DispatchResult(
                channel=channel,
                status=DispatchStatus.FAILED,
                error="recipient has no target for this channel",
            )

        if state == FeatureFlagState.OFF:
            logger.info(
                "communication_dispatch_disabled",
                channel=channel,
                template_code=template_code,
            )
            return DispatchResult(channel=channel, status=DispatchStatus.DISABLED)

        if state == FeatureFlagState.MOCK or channel not in self._providers:
            logger.info(
                "communication_dispatch_mock",
                channel=channel,
                template_code=template_code,
                target=target,
                context_keys=list((context or {}).keys()),
            )
            return DispatchResult(
                channel=channel,
                status=DispatchStatus.MOCKED,
                provider_message_id=f"mock-{template_code}",
            )

        provider = self._providers[channel]
        try:
            return await provider.send(
                recipient=recipient, template_code=template_code, context=context or {}
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "communication_dispatch_failed",
                channel=channel,
                template_code=template_code,
                error=str(exc),
            )
            return DispatchResult(
                channel=channel,
                status=DispatchStatus.FAILED,
                error=str(exc),
            )

    async def fanout(
        self,
        *,
        channel: Channel,
        recipients: list[Recipient],
        template_code: str,
        context: dict[str, Any] | None = None,
    ) -> list[DispatchResult]:
        """Dispatch to many recipients sequentially. Per-recipient failures
        are captured in the result list; one bad number does not abort the
        batch. Callers that need true parallelism should enqueue via
        `arq_worker.notification_fanout`."""
        results: list[DispatchResult] = []
        for r in recipients:
            results.append(
                await self.send(
                    channel=channel,
                    recipient=r,
                    template_code=template_code,
                    context=context,
                )
            )
        return results


# Module-level default instance — callers do `from app.services.notification
# import communication_service`. Real providers register during app
# startup in main.py (STAGE-6-PENDING-sms-live etc.).
communication_service = CommunicationService()


class _SMSGatewayProvider:
    """Adapter from the portal communication surface to ``sms_service``."""

    async def send(
        self,
        *,
        recipient: Recipient,
        template_code: str,
        context: dict[str, Any],
    ) -> DispatchResult:
        if not sms_service.enabled:
            return DispatchResult(
                channel=Channel.SMS,
                status=DispatchStatus.FAILED,
                error="SMS provider is not configured",
            )

        message = str(context.get("message") or "").strip()
        if not message:
            return DispatchResult(
                channel=Channel.SMS,
                status=DispatchStatus.FAILED,
                error="message is required for SMS dispatch",
            )

        success = await sms_service.send_sms(
            to=recipient.phone or "",
            message=message,
        )
        return DispatchResult(
            channel=Channel.SMS,
            status=DispatchStatus.SENT if success else DispatchStatus.FAILED,
            provider_message_id=f"sms-{template_code.lower()}",
            error=None if success else "SMS provider rejected the dispatch",
        )


class _EmailGatewayProvider:
    """Adapter from the portal communication surface to ``email_service``."""

    async def send(
        self,
        *,
        recipient: Recipient,
        template_code: str,
        context: dict[str, Any],
    ) -> DispatchResult:
        if not email_service.enabled:
            return DispatchResult(
                channel=Channel.EMAIL,
                status=DispatchStatus.FAILED,
                error="Email provider is not configured",
            )

        subject = str(context.get("subject") or template_code.replace("_", " ").title()).strip()
        html_body = str(context.get("html_body") or "").strip()
        if not html_body:
            message = str(context.get("message") or "").strip()
            if not message:
                return DispatchResult(
                    channel=Channel.EMAIL,
                    status=DispatchStatus.FAILED,
                    error="email content is required for dispatch",
                )
            html_body = f"<html><body><p>{message}</p></body></html>"

        success = await email_service.send_email(
            to=[recipient.email or ""],
            subject=subject,
            html_body=html_body,
        )
        return DispatchResult(
            channel=Channel.EMAIL,
            status=DispatchStatus.SENT if success else DispatchStatus.FAILED,
            provider_message_id=f"email-{template_code.lower()}",
            error=None if success else "Email provider rejected the dispatch",
        )


class _PushGatewayProvider:
    """Adapter from the portal communication surface to ``push_service``."""

    async def send(
        self,
        *,
        recipient: Recipient,
        template_code: str,
        context: dict[str, Any],
    ) -> DispatchResult:
        if not push_service.enabled:
            return DispatchResult(
                channel=Channel.PUSH,
                status=DispatchStatus.FAILED,
                error="Push provider is not configured",
            )
        if not recipient.device_token:
            return DispatchResult(
                channel=Channel.PUSH,
                status=DispatchStatus.FAILED,
                error="recipient has no device token for push dispatch",
            )

        title = str(context.get("title") or template_code.replace("_", " ").title()).strip()
        body = str(context.get("message") or context.get("body") or "").strip()
        if not body:
            return DispatchResult(
                channel=Channel.PUSH,
                status=DispatchStatus.FAILED,
                error="push body is required for dispatch",
            )

        success = await push_service.send_to_tokens(
            tokens=[recipient.device_token],
            title=title,
            body=body,
            data=context.get("data") if isinstance(context.get("data"), dict) else None,
        )
        success_count = int(success.get("success", 0))
        is_success = success_count > 0
        return DispatchResult(
            channel=Channel.PUSH,
            status=DispatchStatus.SENT if is_success else DispatchStatus.FAILED,
            provider_message_id=f"push-{template_code.lower()}",
            error=None if is_success else "Push provider rejected the dispatch",
        )


communication_service.register_provider(Channel.SMS, _SMSGatewayProvider())
communication_service.register_provider(Channel.EMAIL, _EmailGatewayProvider())
communication_service.register_provider(Channel.PUSH, _PushGatewayProvider())
