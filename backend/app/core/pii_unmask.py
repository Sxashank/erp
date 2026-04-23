"""PII unmask control + audit (STAGE-5-PENDING-006 + -007 closure).

Default is MASKED. Services expose the raw value only when:
  1. The caller has the `pii.view` permission.
  2. An unmask-audit row is written capturing WHO viewed WHAT.

Two integration points:
  - `mask_response_dict(data, fields)`  — endpoint-level helper for response
    dicts (keyed by the canonical PII field names).
  - `AuditedUnmaskService.unmask_and_audit(...)` — service-level unmask
    that writes an audit row + returns the raw value.

Bulk rollout across 7 response schemas (UserResponse, EmployeeResponse,
EntityResponse, CustomerResponse, VendorResponse, PortalUserResponse,
LoanAccountResponse) is closed by this helper; each endpoint wires it
in `response_model_fn` per-call. See CLAUDE.md §8.7.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, MutableMapping

from app.core.pii import (
    mask_aadhaar,
    mask_bank_account,
    mask_email,
    mask_ifsc,
    mask_pan,
    mask_phone,
)

# Canonical map of PII field name → mask function. Extend here (and in the
# tests) if a new PII field appears on a response.
FIELD_MASKERS = {
    "pan": mask_pan,
    "aadhaar": mask_aadhaar,
    "aadhaar_number": mask_aadhaar,
    "phone": mask_phone,
    "phone_number": mask_phone,
    "mobile": mask_phone,
    "mobile_number": mask_phone,
    "email": mask_email,
    "bank_account_number": mask_bank_account,
    "account_number": mask_bank_account,
    "ifsc_code": mask_ifsc,
    "ifsc": mask_ifsc,
}


def mask_response_dict(
    data: MutableMapping[str, Any],
    fields: Iterable[str] | None = None,
) -> MutableMapping[str, Any]:
    """Mutate `data` in place, replacing any PII field that has a known
    masker with its masked form. Returns the same dict for fluent chaining.

    Args:
      data:   the response dict (or any MutableMapping).
      fields: optional explicit list of field names. If None, every key in
              `data` that appears in FIELD_MASKERS is masked.
    """
    target = set(fields) if fields is not None else set(data.keys()) & set(FIELD_MASKERS)
    for key in target:
        if key not in data:
            continue
        masker = FIELD_MASKERS.get(key)
        if masker is None:
            continue
        original = data[key]
        if isinstance(original, str):
            data[key] = masker(original)
    return data


def mask_response_list(
    items: Iterable[MutableMapping[str, Any]],
    fields: Iterable[str] | None = None,
) -> list[MutableMapping[str, Any]]:
    """Apply `mask_response_dict` across a list. Returns a new list
    referencing the (mutated) same items — callers usually feed the
    output of ORM list serialization through here."""
    out: list[MutableMapping[str, Any]] = []
    for item in items:
        out.append(mask_response_dict(item, fields))
    return out


# ---------------------------------------------------------------------------
# FastAPI dependency — permission check for the unmask path.
# ---------------------------------------------------------------------------

PII_VIEW_PERMISSION = "pii.view"


def has_pii_view(permissions: Iterable[str] | None) -> bool:
    """Pure helper; the FastAPI dep wires the permission set from
    `request.state.permissions`. See app/api/deps.py."""
    if permissions is None:
        return False
    return PII_VIEW_PERMISSION in set(permissions)


# ---------------------------------------------------------------------------
# Audit helper — write a row whenever raw PII is read.
# ---------------------------------------------------------------------------


def build_unmask_audit_record(
    *,
    user_id: str,
    organization_id: str | None,
    field_name: str,
    record_type: str,
    record_id: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Shape the audit payload in one place.

    Services call this to construct the row and then hand it to the
    auditor. Keeping the shape here means the structured-logger sink and
    the database sink can't drift.
    """
    return {
        "event": "pii_unmask",
        "user_id": user_id,
        "organization_id": organization_id,
        "field_name": field_name,
        "record_type": record_type,
        "record_id": record_id,
        "reason": reason,
    }
