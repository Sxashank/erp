"""HMAC webhook signature tests (CLAUDE.md §8.6)."""

from __future__ import annotations

import hashlib
import hmac
import time

import pytest

from app.core.webhook_signature import (
    ExpiredSignatureError,
    InvalidSignatureError,
    ReplayedSignatureError,
    compute_hmac_sha256,
    verify_signature,
    verify_timestamp,
    verify_webhook,
)


SECRET = "s" * 64
PAYLOAD = b'{"event":"payment.authorized","amount":10000}'


def _sign(payload: bytes, secret: str = SECRET, encoding: str = "hex") -> str:
    return compute_hmac_sha256(secret, payload, encoding=encoding)


# ---------------------------------------------------------------------------
# Low-level primitives.
# ---------------------------------------------------------------------------

def test_compute_hmac_sha256_hex_matches_stdlib() -> None:
    expected = hmac.new(SECRET.encode(), PAYLOAD, hashlib.sha256).hexdigest()
    assert compute_hmac_sha256(SECRET, PAYLOAD) == expected


def test_compute_hmac_sha256_base64() -> None:
    out = compute_hmac_sha256(SECRET, PAYLOAD, encoding="base64")
    # Base64 of a 32-byte digest is 44 chars with '='.
    assert len(out) == 44 and out.endswith("=")


def test_verify_signature_accepts_matching() -> None:
    assert verify_signature(SECRET, PAYLOAD, _sign(PAYLOAD)) is True


def test_verify_signature_rejects_wrong_secret() -> None:
    wrong = compute_hmac_sha256("other" * 16, PAYLOAD)
    assert verify_signature(SECRET, PAYLOAD, wrong) is False


def test_verify_signature_rejects_tampered_payload() -> None:
    sig = _sign(PAYLOAD)
    tampered = PAYLOAD.replace(b"10000", b"99999")
    assert verify_signature(SECRET, tampered, sig) is False


def test_verify_signature_empty_string_rejected() -> None:
    assert verify_signature(SECRET, PAYLOAD, "") is False


# ---------------------------------------------------------------------------
# Timestamp skew.
# ---------------------------------------------------------------------------

def test_verify_timestamp_within_window() -> None:
    now = 1_700_000_000
    assert verify_timestamp(now - 60, now=now) is True
    assert verify_timestamp(now + 60, now=now) is True
    assert verify_timestamp(now - 299, now=now) is True
    assert verify_timestamp(now + 299, now=now) is True


def test_verify_timestamp_outside_window() -> None:
    now = 1_700_000_000
    assert verify_timestamp(now - 301, now=now) is False
    assert verify_timestamp(now + 301, now=now) is False


def test_verify_timestamp_rejects_garbage() -> None:
    assert verify_timestamp("not-a-number") is False
    assert verify_timestamp(None) is False


# ---------------------------------------------------------------------------
# Full webhook verification.
# ---------------------------------------------------------------------------

def test_verify_webhook_happy_path() -> None:
    now = int(time.time())
    result = verify_webhook(
        secret=SECRET,
        payload=PAYLOAD,
        provided_signature=_sign(PAYLOAD),
        provided_timestamp=now,
        now=now,
    )
    assert result.verified is True


def test_verify_webhook_raises_on_missing_signature() -> None:
    with pytest.raises(InvalidSignatureError) as exc:
        verify_webhook(
            secret=SECRET,
            payload=PAYLOAD,
            provided_signature=None,
            provided_timestamp=int(time.time()),
        )
    assert exc.value.error_code == "INVALID_WEBHOOK_SIGNATURE"


def test_verify_webhook_raises_on_bad_signature() -> None:
    with pytest.raises(InvalidSignatureError):
        verify_webhook(
            secret=SECRET,
            payload=PAYLOAD,
            provided_signature="deadbeef" * 8,
            provided_timestamp=int(time.time()),
        )


def test_verify_webhook_raises_on_expired_timestamp() -> None:
    with pytest.raises(ExpiredSignatureError) as exc:
        verify_webhook(
            secret=SECRET,
            payload=PAYLOAD,
            provided_signature=_sign(PAYLOAD),
            provided_timestamp=1_700_000_000,
            now=1_700_000_000 + 3600,  # 1 hour later
        )
    assert exc.value.error_code == "WEBHOOK_TIMESTAMP_EXPIRED"


def test_verify_webhook_raises_on_missing_timestamp() -> None:
    with pytest.raises(ExpiredSignatureError):
        verify_webhook(
            secret=SECRET,
            payload=PAYLOAD,
            provided_signature=_sign(PAYLOAD),
            provided_timestamp=None,
        )


def test_verify_webhook_rejects_replay() -> None:
    seen_nonces = {"nonce-0001", "nonce-0002"}
    with pytest.raises(ReplayedSignatureError):
        verify_webhook(
            secret=SECRET,
            payload=PAYLOAD,
            provided_signature=_sign(PAYLOAD),
            provided_timestamp=int(time.time()),
            nonce_store=seen_nonces,
            nonce="nonce-0001",
        )


def test_verify_webhook_allows_first_use_of_nonce() -> None:
    seen_nonces: set[str] = set()
    result = verify_webhook(
        secret=SECRET,
        payload=PAYLOAD,
        provided_signature=_sign(PAYLOAD),
        provided_timestamp=int(time.time()),
        nonce_store=seen_nonces,
        nonce="nonce-first",
    )
    assert result.verified is True


def test_verify_webhook_base64_signature() -> None:
    sig = _sign(PAYLOAD, encoding="base64")
    result = verify_webhook(
        secret=SECRET,
        payload=PAYLOAD,
        provided_signature=sig,
        provided_timestamp=int(time.time()),
        encoding="base64",
    )
    assert result.verified is True
