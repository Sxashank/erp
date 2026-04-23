"""Regression tests ensuring GST portal passwords are encrypted at rest.

See CLAUDE.md §6.8 and §12.1 (known violation now closed). These tests do
not hit the DB; they verify the service writes the encrypted form to the
model attribute and that Fernet round-trips.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.encryption import decrypt_value, encrypt_value
from app.services.gst.gst_registration_service import GSTRegistrationService


def test_fernet_round_trip() -> None:
    """encrypt_value(x) != x and decrypt_value(encrypt_value(x)) == x."""
    plaintext = "super-secret-gstn-portal-password!@#"

    ciphertext = encrypt_value(plaintext)

    assert ciphertext != plaintext
    assert decrypt_value(ciphertext) == plaintext


def test_fernet_empty_input_returns_empty() -> None:
    """Empty strings are preserved (no ciphertext produced)."""
    assert encrypt_value("") == ""
    assert decrypt_value("") == ""


def test_fernet_ciphertext_is_nondeterministic() -> None:
    """Fernet includes a random IV — two encryptions of the same value differ."""
    plaintext = "same-value"

    a = encrypt_value(plaintext)
    b = encrypt_value(plaintext)

    assert a != b
    assert decrypt_value(a) == plaintext
    assert decrypt_value(b) == plaintext


@pytest.mark.asyncio
async def test_create_encrypts_e_invoice_password(monkeypatch) -> None:
    """Service.create must write the encrypted form to the model."""
    # Arrange
    session = AsyncMock()
    # No existing record
    async def _no_existing(_gstin):
        return None

    class _Repo:
        def __init__(self, _s):
            pass

        async def get_by_gstin(self, _gstin):  # noqa: D401
            return None

    monkeypatch.setattr(
        "app.services.gst.gst_registration_service.GSTRegistrationRepository",
        _Repo,
    )

    captured = {}

    def _fake_model(**kwargs):
        captured.update(kwargs)
        m = MagicMock()
        for k, v in kwargs.items():
            setattr(m, k, v)
        return m

    monkeypatch.setattr(
        "app.services.gst.gst_registration_service.GSTRegistration",
        _fake_model,
    )

    data = MagicMock()
    data.gstin = "27AAAAA0000A1Z5"
    plaintext_password = "portal-password-123"
    data.e_invoice_password = plaintext_password
    data.model_dump = MagicMock(
        return_value={
            "gstin": "27AAAAA0000A1Z5",
            "organization_id": uuid4(),
        }
    )

    svc = GSTRegistrationService(session)

    # Act
    await svc.create(data, created_by=uuid4())

    # Assert
    assert "e_invoice_password_encrypted" in captured
    encrypted = captured["e_invoice_password_encrypted"]
    assert encrypted != plaintext_password
    assert decrypt_value(encrypted) == plaintext_password
