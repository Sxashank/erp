"""Tenant-aware webhook gate tests (STAGE-5-PENDING-005 closure).

Pins the contract between the webhook routers and the IntegrationConfig
tenant-secrets store. Coverage:

  * Happy path — valid HMAC signature verifies against the tenant's stored
    secret (NOT env) and returns a trusted envelope.
  * Missing config row → `WebhookConfigurationError` (400, not 500, because
    the fix is operational).
  * Empty `webhook_signing_secret` field → same.
  * Missing signature header → `InvalidSignatureError`.
  * Wrong HMAC → `InvalidSignatureError`.
  * Expired timestamp → `ExpiredSignatureError`.
  * Base64 encoding honoured when `signature_encoding` is set.

All tests mock the session and `IntegrationService.get_by_type` — the gate's
contract is purely "read config, run verify_webhook". A live DB would only
add noise.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.webhook_gate import (
    SIGNATURE_ENCODING_KEY,
    SIGNING_SECRET_KEY,
    WebhookConfigurationError,
    verify_tenant_webhook,
)
from app.core.webhook_signature import (
    ExpiredSignatureError,
    InvalidSignatureError,
)
from app.models.core.integration_config import (
    IntegrationProvider,
    IntegrationType,
)

# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _hmac_hex(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _hmac_b64(secret: str, body: bytes) -> str:
    import base64

    return base64.b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).decode()


def _fake_config(
    *,
    secret: str | None = "tenant-shared-secret",
    encoding: str | None = None,
) -> SimpleNamespace:
    data = {}
    if secret is not None:
        data[SIGNING_SECRET_KEY] = secret
    if encoding is not None:
        data[SIGNATURE_ENCODING_KEY] = encoding
    return SimpleNamespace(id=uuid4(), config_data=data)


def _patch_service(config_returned):
    """Short helper: patch IntegrationService.get_by_type to return `config_returned`."""
    return patch(
        "app.services.core.integration_service.IntegrationService.get_by_type",
        new=AsyncMock(return_value=config_returned),
    )


# ---------------------------------------------------------------------------
# Happy path.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verifies_hex_signature_against_tenant_secret() -> None:
    body = b'{"event": "payment.captured", "id": "pay_123"}'
    secret = "tenant-razorpay-secret"
    cfg = _fake_config(secret=secret)
    org = uuid4()

    with _patch_service(cfg):
        envelope = await verify_tenant_webhook(
            session=AsyncMock(),
            organization_id=org,
            integration_type=IntegrationType.PAYMENT_GATEWAY,
            provider=IntegrationProvider.RAZORPAY,
            vendor_label="Razorpay",
            body=body,
            signature=_hmac_hex(secret, body),
            timestamp=str(int(time.time())),
        )

    assert envelope.organization_id == org
    assert envelope.integration_config_id == cfg.id
    assert envelope.body == body
    assert envelope.vendor == "Razorpay"


@pytest.mark.asyncio
async def test_omitted_timestamp_substitutes_now() -> None:
    """Razorpay historical doesn't send a timestamp. Gate must not reject that."""
    body = b'{"ok": true}'
    secret = "secret"
    cfg = _fake_config(secret=secret)

    with _patch_service(cfg):
        envelope = await verify_tenant_webhook(
            session=AsyncMock(),
            organization_id=uuid4(),
            integration_type=IntegrationType.PAYMENT_GATEWAY,
            provider=IntegrationProvider.RAZORPAY,
            vendor_label="Razorpay",
            body=body,
            signature=_hmac_hex(secret, body),
            timestamp=None,
        )
    assert envelope.vendor == "Razorpay"


@pytest.mark.asyncio
async def test_base64_encoding_honoured() -> None:
    body = b'{"event": "charge"}'
    secret = "secret"
    cfg = _fake_config(secret=secret, encoding="base64")

    with _patch_service(cfg):
        envelope = await verify_tenant_webhook(
            session=AsyncMock(),
            organization_id=uuid4(),
            integration_type=IntegrationType.CREDIT_BUREAU,
            provider=IntegrationProvider.CIBIL,
            vendor_label="CIBIL",
            body=body,
            signature=_hmac_b64(secret, body),
            timestamp=str(int(time.time())),
        )
    assert envelope.vendor == "CIBIL"


# ---------------------------------------------------------------------------
# Configuration errors → 400 with WEBHOOK_NOT_CONFIGURED.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_missing_integration_config_surfaces_operational_error() -> None:
    with _patch_service(None):
        with pytest.raises(WebhookConfigurationError) as exc:
            await verify_tenant_webhook(
                session=AsyncMock(),
                organization_id=uuid4(),
                integration_type=IntegrationType.PAYMENT_GATEWAY,
                provider=IntegrationProvider.RAZORPAY,
                vendor_label="Razorpay",
                body=b"{}",
                signature="anything",
            )
    assert exc.value.vendor == "Razorpay"
    assert exc.value.error_code == "WEBHOOK_NOT_CONFIGURED"


@pytest.mark.asyncio
async def test_empty_signing_secret_field_surfaces_operational_error() -> None:
    cfg = _fake_config(secret=None)  # config row exists but the key is missing

    with _patch_service(cfg):
        with pytest.raises(WebhookConfigurationError) as exc:
            await verify_tenant_webhook(
                session=AsyncMock(),
                organization_id=uuid4(),
                integration_type=IntegrationType.PAYMENT_GATEWAY,
                provider=IntegrationProvider.RAZORPAY,
                vendor_label="Razorpay",
                body=b"{}",
                signature="anything",
            )
    assert "webhook_signing_secret" in str(exc.value)


# ---------------------------------------------------------------------------
# Signature / timestamp errors → InvalidSignatureError / ExpiredSignatureError.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_missing_signature_header_short_circuits_before_db_read() -> None:
    """Missing signature → raise before we even bother reading the config.

    This saves a DB round-trip for spray-and-pray bots hitting the endpoint.
    """
    service_mock = AsyncMock()
    with patch(
        "app.services.core.integration_service.IntegrationService.get_by_type",
        new=service_mock,
    ):
        with pytest.raises(InvalidSignatureError):
            await verify_tenant_webhook(
                session=AsyncMock(),
                organization_id=uuid4(),
                integration_type=IntegrationType.PAYMENT_GATEWAY,
                provider=IntegrationProvider.RAZORPAY,
                vendor_label="Razorpay",
                body=b"{}",
                signature="",  # missing
            )
    service_mock.assert_not_called()


@pytest.mark.asyncio
async def test_wrong_hmac_raises_invalid_signature() -> None:
    cfg = _fake_config(secret="actual-secret")
    with _patch_service(cfg):
        with pytest.raises(InvalidSignatureError):
            await verify_tenant_webhook(
                session=AsyncMock(),
                organization_id=uuid4(),
                integration_type=IntegrationType.PAYMENT_GATEWAY,
                provider=IntegrationProvider.RAZORPAY,
                vendor_label="Razorpay",
                body=b'{"event": "x"}',
                signature=_hmac_hex("wrong-secret", b'{"event": "x"}'),
                timestamp=str(int(time.time())),
            )


@pytest.mark.asyncio
async def test_expired_timestamp_raises_expired_signature() -> None:
    """Stale timestamp (> 5 min ago) is rejected even with valid HMAC.

    Replay defense: a valid signature from a recorded webhook can't be
    accepted a week later.
    """
    body = b'{"event": "charge"}'
    secret = "secret"
    cfg = _fake_config(secret=secret)
    stale = str(int(time.time()) - 3600)  # 1 hour old

    with _patch_service(cfg):
        with pytest.raises(ExpiredSignatureError):
            await verify_tenant_webhook(
                session=AsyncMock(),
                organization_id=uuid4(),
                integration_type=IntegrationType.PAYMENT_GATEWAY,
                provider=IntegrationProvider.RAZORPAY,
                vendor_label="Razorpay",
                body=body,
                signature=_hmac_hex(secret, body),
                timestamp=stale,
            )
