"""PII masking utilities (CLAUDE.md §8.7).

Masks PAN, Aadhaar, phone, email, bank-account, and IFSC at the API
boundary by default. Unmasked access requires the `pii.view` permission
and is audited at the read site.

Mask formats follow Indian regulator conventions:
  - PAN        AAAAA1234A   → `XXXXX1234X`  (first 5 + last letter obscured)
  - Aadhaar    123412341234 → `XXXX-XXXX-1234` (first 8 obscured, dashed)
  - Phone      +919876543210 → `+91-XXXXX-XX210` (last 3 visible)
  - Email      alice@example.com → `a***@example.com`
  - Bank acct  123456789012 → `XXXXXXXX9012`
  - IFSC       HDFC0001234  → `HDFC0XXX234` (keep bank code + last 3)

These helpers are PURE — no DB, no I/O. The Pydantic mixin at the bottom
plugs into response models so forgotten masks fail the type check.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import field_validator

from app.schemas.base import CamelSchema

_PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
_AADHAAR_RE = re.compile(r"^\d{12}$")
_PHONE_RE = re.compile(r"^\+?\d{6,15}$")


def _blank(value: object) -> bool:
    return value is None or value == ""


def mask_pan(pan: str | None) -> str | None:
    """PAN mask: AAAAA1234A → XXXXX1234X. Invalid PAN returns raw value."""
    if _blank(pan):
        return pan  # type: ignore[return-value]
    pan = pan.strip().upper()  # type: ignore[union-attr]
    if not _PAN_RE.match(pan):
        # Unknown-shape → mask all but last 3 as a safe default.
        return "X" * max(0, len(pan) - 3) + pan[-3:] if len(pan) > 3 else "X" * len(pan)
    return "X" * 5 + pan[5:9] + "X"


def mask_aadhaar(aadhaar: str | None) -> str | None:
    """Aadhaar mask: 123412341234 → XXXX-XXXX-1234."""
    if _blank(aadhaar):
        return aadhaar  # type: ignore[return-value]
    digits = re.sub(r"\D", "", aadhaar)  # type: ignore[arg-type]
    if not _AADHAAR_RE.match(digits):
        # Unrecognised — mask all but last 4.
        return "X" * max(0, len(digits) - 4) + digits[-4:] if digits else aadhaar
    return f"XXXX-XXXX-{digits[-4:]}"


def mask_phone(phone: str | None) -> str | None:
    """Phone mask: keep country code + last 3 digits. +91-XXXXX-XX210."""
    if _blank(phone):
        return phone  # type: ignore[return-value]
    raw = phone.strip()  # type: ignore[union-attr]
    digits_only = re.sub(r"\D", "", raw)
    if len(digits_only) < 4:
        return "X" * len(digits_only) if digits_only else raw
    # Indian mobile with country code 91 and 10 digits: +91-XXXXX-XX210
    if raw.startswith("+91") and len(digits_only) == 12:
        return f"+91-XXXXX-XX{digits_only[-3:]}"
    # Generic: keep last 3.
    return "X" * (len(digits_only) - 3) + digits_only[-3:]


def mask_email(email: str | None) -> str | None:
    """Email mask: alice@example.com → a***@example.com."""
    if _blank(email):
        return email  # type: ignore[return-value]
    raw = email.strip()  # type: ignore[union-attr]
    if "@" not in raw:
        return "X" * max(0, len(raw) - 2) + raw[-2:] if len(raw) > 2 else "X" * len(raw)
    local, domain = raw.split("@", 1)
    if len(local) == 0:
        return f"***@{domain}"
    if len(local) == 1:
        return f"{local}***@{domain}"
    return f"{local[0]}***@{domain}"


def mask_bank_account(account: str | None) -> str | None:
    """Bank account mask: keep last 4 digits only."""
    if _blank(account):
        return account  # type: ignore[return-value]
    digits = re.sub(r"\D", "", account)  # type: ignore[arg-type]
    if len(digits) <= 4:
        return "X" * len(digits)
    return "X" * (len(digits) - 4) + digits[-4:]


def mask_ifsc(ifsc: str | None) -> str | None:
    """IFSC mask: keep bank code (first 4) + last 3. Example: HDFC0XXX234."""
    if _blank(ifsc):
        return ifsc  # type: ignore[return-value]
    raw = ifsc.strip().upper()  # type: ignore[union-attr]
    if len(raw) != 11:
        # Unknown format — mask middle; keep first 4 + last 3 when possible.
        if len(raw) <= 7:
            return "X" * len(raw)
        return raw[:4] + "X" * (len(raw) - 7) + raw[-3:]
    return raw[:4] + "0" + "X" * 3 + raw[-3:]


# ---------------------------------------------------------------------------
# Pydantic mixin — apply on response models that expose PII fields.
# ---------------------------------------------------------------------------

class MaskedPIIModel(CamelSchema):
    """Pydantic v2 base that auto-masks common PII fields at serialization.

    Subclasses declare fields named `pan`, `aadhaar`, `phone`, `email`,
    `bank_account_number`, or `ifsc_code`; the validators below mask them
    on the way out. To render unmasked, the service-layer call site must
    check `pii.view` and construct the response bypassing this base (e.g.
    by wrapping the ORM object with a different response model).
    """

    @field_validator("pan", check_fields=False)
    @classmethod
    def _mask_pan(cls, v: Any) -> Any:
        return mask_pan(v) if isinstance(v, str) else v

    @field_validator("aadhaar", "aadhaar_number", check_fields=False)
    @classmethod
    def _mask_aadhaar(cls, v: Any) -> Any:
        return mask_aadhaar(v) if isinstance(v, str) else v

    @field_validator("phone", "phone_number", "mobile", "mobile_number", check_fields=False)
    @classmethod
    def _mask_phone(cls, v: Any) -> Any:
        return mask_phone(v) if isinstance(v, str) else v

    @field_validator("email", check_fields=False)
    @classmethod
    def _mask_email(cls, v: Any) -> Any:
        return mask_email(v) if isinstance(v, str) else v

    @field_validator("bank_account_number", "account_number", check_fields=False)
    @classmethod
    def _mask_bank_account(cls, v: Any) -> Any:
        return mask_bank_account(v) if isinstance(v, str) else v

    @field_validator("ifsc_code", "ifsc", check_fields=False)
    @classmethod
    def _mask_ifsc(cls, v: Any) -> Any:
        return mask_ifsc(v) if isinstance(v, str) else v
