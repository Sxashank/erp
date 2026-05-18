"""Tenant-aware webhook verification gate (STAGE-5-PENDING-005 closure).

Every inbound webhook follows the same gate:

    1. Pull the tenant's signing secret from ``IntegrationConfig``
       (keyed by organization_id + integration_type + provider) —
       NEVER from env. See CLAUDE.md §6.8 and §12.24.
    2. Run HMAC + timestamp verification via
       :func:`app.core.webhook_signature.verify_webhook`.
    3. Return a :class:`WebhookVerified` record the handler can trust.

Handlers stay thin: they call this gate, then dispatch to their domain
service. If the signature is missing or wrong, the gate raises a typed
:class:`~app.core.webhook_signature.InvalidSignatureError` which the
error middleware turns into a 400 with ``error_code=INVALID_WEBHOOK_SIGNATURE``.

This module is imported by every webhook router under
``app/api/v1/webhooks/*`` so changes here flow everywhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException
from app.core.webhook_signature import (
    InvalidSignatureError,
    verify_webhook,
)
from app.models.core.integration_config import (
    IntegrationProvider,
    IntegrationType,
)

# ---------------------------------------------------------------------------
# IntegrationConfig keys every vendor secret lives under.
# This centralises the naming so the field a tenant fills in the admin UI
# matches what the webhook handler reads at runtime.
# ---------------------------------------------------------------------------

SIGNING_SECRET_KEY: Final[str] = "webhook_signing_secret"
SIGNATURE_ENCODING_KEY: Final[str] = "signature_encoding"  # "hex" or "base64"


class WebhookConfigurationError(BadRequestException):
    """Raised when IntegrationConfig for this vendor is missing or incomplete.

    Surfaced as 400 (not 500) because the fix is operational — the NBFC
    needs to provision the vendor credentials through the admin UI before
    webhooks can land. Treating it as a server error would mask the
    configuration gap and confuse the on-call rotation.
    """

    def __init__(
        self,
        *,
        vendor: str,
        reason: str,
    ) -> None:
        super().__init__(
            detail=f"{vendor} webhook config missing: {reason}",
            error_code="WEBHOOK_NOT_CONFIGURED",
        )
        self.vendor = vendor


@dataclass(frozen=True)
class WebhookVerified:
    """What the gate returns on success. Handler downstream can trust these."""

    organization_id: UUID
    integration_config_id: UUID
    body: bytes
    vendor: str


async def verify_tenant_webhook(
    *,
    session: AsyncSession,
    organization_id: UUID,
    integration_type: IntegrationType,
    provider: IntegrationProvider | None,
    vendor_label: str,  # "Razorpay" / "Paytm" / ... — used in errors + logs
    body: bytes,
    signature: str,
    timestamp: str | None = None,
    max_age_seconds: int = 300,
) -> WebhookVerified:
    """One-shot gate: load secret, verify signature, return trusted envelope.

    Raises:
        :class:`WebhookConfigurationError` — IntegrationConfig missing or the
            signing-secret field is empty. Fix by provisioning in admin UI.
        :class:`~app.core.webhook_signature.InvalidSignatureError` — HMAC or
            timestamp check failed. Do NOT retry the upstream send; the
            payload was spoofed or corrupt.

    Note: we import the service lazily so this module has no circular
    dependency with integration_service (which itself imports exception types).
    """
    if not signature:
        raise InvalidSignatureError(
            detail=f"{vendor_label} webhook missing signature header",
        )

    # Lazy import — avoids circular import with service / model layers.
    from app.services.core.integration_service import IntegrationService

    service = IntegrationService(session)
    config = await service.get_by_type(
        organization_id=organization_id,
        integration_type=integration_type,
        provider=provider,
        decrypt=True,
    )
    if config is None:
        raise WebhookConfigurationError(
            vendor=vendor_label,
            reason="no IntegrationConfig row for this organization + type + provider",
        )

    config_data = config.config_data or {}
    secret = config_data.get(SIGNING_SECRET_KEY)
    if not secret:
        raise WebhookConfigurationError(
            vendor=vendor_label,
            reason=f"'{SIGNING_SECRET_KEY}' not set on IntegrationConfig",
        )

    encoding = config_data.get(SIGNATURE_ENCODING_KEY, "hex")

    # Some vendors (Razorpay historical) don't send a timestamp header. In
    # that narrow case we substitute "now" so the skew check trivially passes
    # — the HMAC check still catches spoofed payloads.
    import time as _time

    ts: str | int = timestamp if timestamp is not None else int(_time.time())

    # Defer to the primitive — it raises InvalidSignatureError / ExpiredSignatureError
    # on any failure, both of which surface as 400 with matching error_code.
    verify_webhook(
        secret=secret,
        payload=body,
        provided_signature=signature,
        provided_timestamp=ts,
        max_skew_seconds=max_age_seconds,
        encoding=encoding,
    )

    return WebhookVerified(
        organization_id=organization_id,
        integration_config_id=config.id,
        body=body,
        vendor=vendor_label,
    )
