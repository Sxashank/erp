"""Tenant-secret storage contract (CLAUDE.md §1 + §6.8 + §12.24).

This codebase is a multi-tenant SaaS. Tenant-owned secrets (per-NBFC
Razorpay key, GSTN portal password, bureau API key, NACH corporate ID,
SMS sender credentials, etc.) MUST live in Fernet-encrypted DB rows,
NOT env vars. The canonical mechanism is `IntegrationConfig` at
`sys_integration_config`.

These tests pin three properties so the rule can't drift:
  1. The Settings class (env / pydantic-settings) exposes NO
     client-specific secret fields.
  2. `EncryptionService.encrypt_dict` round-trips values and produces
     ciphertext that doesn't reveal the plaintext.
  3. `IntegrationService` uses `encrypt_dict` before persisting + flags
     the decrypt path behind an explicit `decrypt=True` argument.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.config import settings
from app.core.encryption import encryption_service


# ---------------------------------------------------------------------------
# Platform vs tenant: the env-backed Settings class must NOT carry any
# value that belongs to a specific NBFC / tenant.
# ---------------------------------------------------------------------------


# Keys that would be tenant-owned if they ever landed in env. If any of
# these appear as Settings fields, Stage-12.24 is violated.
_BANNED_ENV_FIELDS = (
    "RAZORPAY_KEY",
    "RAZORPAY_SECRET",
    "RAZORPAY_API_KEY",
    "PAYTM_API_KEY",
    "CCAVENUE_API_KEY",
    "MSG91_AUTH_KEY",
    "MSG91_API_KEY",
    "FCM_SERVER_KEY",
    "APNS_AUTH_KEY",
    "CIBIL_API_KEY",
    "EXPERIAN_API_KEY",
    "CRIF_API_KEY",
    "CKYC_USERNAME",
    "CKYC_PASSWORD",
    "GSTN_USERNAME",
    "GSTN_PASSWORD",
    "TRACES_USERNAME",
    "TRACES_PASSWORD",
    "NSDL_USERNAME",
    "NSDL_PASSWORD",
    "NACH_CORPORATE_ID",
    "NACH_CORPORATE_USER_NAME",
    "NACH_CORPORATE_PASSWORD",
    "CERSAI_USERNAME",
    "CERSAI_PASSWORD",
    "NESL_API_KEY",
    "ESIGN_API_KEY",
)


def test_env_settings_hold_no_tenant_scoped_secret_fields() -> None:
    """Scan `settings` for any attribute matching the banned-vendor list.
    Using `dir()` because pydantic-settings surfaces fields as attributes.
    """
    attrs = {a.upper() for a in dir(settings) if not a.startswith("_")}
    violations = attrs & set(_BANNED_ENV_FIELDS)
    assert not violations, (
        f"Tenant-scoped secret(s) leaked into `app.config.Settings`: {violations}. "
        f"These belong in per-org Fernet-encrypted DB rows "
        f"(see CLAUDE.md §6.8 and §12.24)."
    )


def test_only_platform_secrets_shapes_exist_in_settings() -> None:
    """Smoke-test that the expected PLATFORM secrets exist. If someone
    removed JWT_SECRET_KEY or ENCRYPTION_KEY we have bigger problems."""
    # These must be present — they're platform.
    assert hasattr(settings, "JWT_SECRET_KEY")
    # Optional but common — allow any of these to be absent but confirm
    # the shape of `settings` is sensible.
    expected_platform = {"DATABASE_URL", "REDIS_URL", "APP_NAME", "APP_ENV"}
    present = {a for a in dir(settings) if not a.startswith("_")}
    # At least 2 of the 4 expected — sanity, not strict.
    assert len(expected_platform & present) >= 2


# ---------------------------------------------------------------------------
# Encryption primitive — tenant secrets must round-trip and the ciphertext
# must not equal the plaintext (otherwise we're "encrypting" with no-op).
# ---------------------------------------------------------------------------


def test_encryption_round_trips() -> None:
    secret = "razorpay-merchant-secret-12345"
    cipher = encryption_service.encrypt(secret)
    assert cipher != secret
    assert encryption_service.decrypt(cipher) == secret


def test_encryption_produces_different_ciphertext_per_call() -> None:
    """Fernet adds a timestamp + IV, so two encryptions of the same value
    produce different ciphertexts — this is what protects us from
    frequency analysis across rows."""
    secret = "api-key"
    c1 = encryption_service.encrypt(secret)
    c2 = encryption_service.encrypt(secret)
    assert c1 != c2
    assert encryption_service.decrypt(c1) == secret
    assert encryption_service.decrypt(c2) == secret


def test_encrypt_dict_only_touches_listed_keys() -> None:
    data = {
        "api_key": "secret-value",
        "merchant_id": "mid-42",  # NOT sensitive
        "sandbox_url": "https://api.example.com/sandbox",  # NOT sensitive
    }
    out = encryption_service.encrypt_dict(data, sensitive_keys=["api_key"])
    assert out["merchant_id"] == "mid-42"
    assert out["sandbox_url"] == "https://api.example.com/sandbox"
    assert out["api_key"] != "secret-value"
    # Decrypt recovers the original.
    recovered = encryption_service.decrypt_dict(out, sensitive_keys=["api_key"])
    assert recovered["api_key"] == "secret-value"


def test_encrypt_dict_skips_missing_and_falsy_keys() -> None:
    data = {"api_key": "", "other": None}
    out = encryption_service.encrypt_dict(data, sensitive_keys=["api_key", "nonexistent"])
    # Empty string is falsy → not encrypted (stays empty).
    assert out["api_key"] == ""
    # Missing key is silently ignored.
    assert "nonexistent" not in out


# ---------------------------------------------------------------------------
# IntegrationService — the default read path must NOT decrypt. Callers must
# opt in with `decrypt=True`. This prevents accidental leaks through list
# endpoints or debug dumps.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_integration_service_get_does_not_decrypt_by_default() -> None:
    """`IntegrationService.get(id)` with no `decrypt=True` argument must
    return the row with `config_data` still encrypted. Services that
    actually need the raw value pass `decrypt=True` explicitly."""
    from unittest.mock import AsyncMock
    from uuid import uuid4

    from app.models.core.integration_config import IntegrationType
    from app.services.core.integration_service import IntegrationService

    svc = IntegrationService(session=MagicMock())
    svc.repo = MagicMock()
    cipher_value = encryption_service.encrypt("secret-value")
    config_id = uuid4()

    def _fresh_config():
        c = MagicMock()
        # PAYMENT_GATEWAY's sensitive fields: api_secret, key_secret, webhook_secret
        c.config_data = {"api_secret": cipher_value}
        c.integration_type = IntegrationType.PAYMENT_GATEWAY
        return c

    # No decrypt= argument → default masks `api_secret`. The raw plaintext
    # must NOT appear in the returned dict — even in the stringified form.
    svc.repo.get = AsyncMock(return_value=_fresh_config())
    result = await svc.get(config_id)
    assert "secret-value" not in str(result.config_data)
    assert "*" in str(result.config_data["api_secret"])

    # Explicit decrypt=True bypasses the mask + decrypts via Fernet.
    svc.repo.get = AsyncMock(return_value=_fresh_config())
    result2 = await svc.get(config_id, decrypt=True)
    assert result2.config_data["api_secret"] == "secret-value"
