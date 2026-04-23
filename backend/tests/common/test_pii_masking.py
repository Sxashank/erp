"""PII masking tests (CLAUDE.md §8.7)."""

from __future__ import annotations

import pytest

from app.core.pii import (
    MaskedPIIModel,
    mask_aadhaar,
    mask_bank_account,
    mask_email,
    mask_ifsc,
    mask_pan,
    mask_phone,
)


# ---------------------------------------------------------------------------
# PAN.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "pan,expected",
    [
        ("ABCDE1234F", "XXXXX1234X"),
        ("XYZAB9876Z", "XXXXX9876X"),
        ("abcde1234f", "XXXXX1234X"),  # case-normalized
    ],
)
def test_mask_pan_valid(pan: str, expected: str) -> None:
    assert mask_pan(pan) == expected


def test_mask_pan_empty_or_none() -> None:
    assert mask_pan(None) is None
    assert mask_pan("") == ""


def test_mask_pan_invalid_shape_still_masks() -> None:
    """Unknown-shape PAN is masked to last 3 chars to stay safe."""
    assert mask_pan("INVALID") == "XXXXLID"


# ---------------------------------------------------------------------------
# Aadhaar.
# ---------------------------------------------------------------------------

def test_mask_aadhaar_valid() -> None:
    assert mask_aadhaar("123412341234") == "XXXX-XXXX-1234"


def test_mask_aadhaar_with_separators_stripped() -> None:
    assert mask_aadhaar("1234-1234-1234") == "XXXX-XXXX-1234"
    assert mask_aadhaar("1234 1234 1234") == "XXXX-XXXX-1234"


def test_mask_aadhaar_empty() -> None:
    assert mask_aadhaar("") == ""
    assert mask_aadhaar(None) is None


def test_mask_aadhaar_invalid_length() -> None:
    """A 10-digit garbage string still masks all but last 4."""
    assert mask_aadhaar("1234567890") == "XXXXXX7890"


# ---------------------------------------------------------------------------
# Phone.
# ---------------------------------------------------------------------------

def test_mask_phone_indian_with_country_code() -> None:
    assert mask_phone("+919876543210") == "+91-XXXXX-XX210"


def test_mask_phone_generic_keeps_last_3() -> None:
    assert mask_phone("9876543210") == "XXXXXXX210"


def test_mask_phone_short_string_masks_all() -> None:
    assert mask_phone("12") == "XX"


def test_mask_phone_empty() -> None:
    assert mask_phone("") == ""
    assert mask_phone(None) is None


# ---------------------------------------------------------------------------
# Email.
# ---------------------------------------------------------------------------

def test_mask_email_typical() -> None:
    assert mask_email("alice@example.com") == "a***@example.com"


def test_mask_email_single_char_local() -> None:
    assert mask_email("a@example.com") == "a***@example.com"


def test_mask_email_empty_local() -> None:
    assert mask_email("@example.com") == "***@example.com"


def test_mask_email_no_at_sign() -> None:
    assert mask_email("bogus") == "XXXus"


def test_mask_email_empty() -> None:
    assert mask_email("") == ""
    assert mask_email(None) is None


# ---------------------------------------------------------------------------
# Bank account + IFSC.
# ---------------------------------------------------------------------------

def test_mask_bank_account_keeps_last_4() -> None:
    assert mask_bank_account("123456789012") == "XXXXXXXX9012"


def test_mask_bank_account_short() -> None:
    assert mask_bank_account("1234") == "XXXX"


def test_mask_ifsc_standard() -> None:
    # IFSC is 11 chars: 4-letter bank code + "0" + 6 char branch code.
    # Mask: first 4 + "0" + 3 X + last 3 = 11 chars.
    assert mask_ifsc("HDFC0001234") == "HDFC0XXX234"
    assert len(mask_ifsc("HDFC0001234")) == 11


def test_mask_ifsc_empty() -> None:
    assert mask_ifsc("") == ""
    assert mask_ifsc(None) is None


# ---------------------------------------------------------------------------
# Pydantic mixin — proves the validators wire onto response models.
# ---------------------------------------------------------------------------

class _UserResponse(MaskedPIIModel):
    full_name: str
    pan: str | None = None
    aadhaar: str | None = None
    phone: str | None = None
    email: str | None = None
    bank_account_number: str | None = None
    ifsc_code: str | None = None


def test_masked_pii_model_masks_on_construction() -> None:
    user = _UserResponse(
        full_name="Alice",
        pan="ABCDE1234F",
        aadhaar="123412341234",
        phone="+919876543210",
        email="alice@example.com",
        bank_account_number="55555577778888",
        ifsc_code="HDFC0001234",
    )
    # Every PII field is masked at validation time.
    assert user.pan == "XXXXX1234X"
    assert user.aadhaar == "XXXX-XXXX-1234"
    assert user.phone == "+91-XXXXX-XX210"
    assert user.email == "a***@example.com"
    assert user.bank_account_number == "XXXXXXXXXX8888"
    assert user.ifsc_code == "HDFC0XXX234"
    # Non-PII passes through untouched.
    assert user.full_name == "Alice"


def test_masked_pii_model_tolerates_missing_fields() -> None:
    user = _UserResponse(full_name="Nobody")
    assert user.pan is None
    assert user.phone is None
    assert user.email is None
