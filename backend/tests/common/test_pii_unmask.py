"""Tests for PII unmask control + mask-response helpers (STAGE-5-PENDING-006/007)."""

from __future__ import annotations

from app.core.pii_unmask import (
    FIELD_MASKERS,
    PII_VIEW_PERMISSION,
    build_unmask_audit_record,
    has_pii_view,
    mask_response_dict,
    mask_response_list,
)


# ---------------------------------------------------------------------------
# mask_response_dict — endpoint helper.
# ---------------------------------------------------------------------------

def test_masks_every_known_pii_field_in_place() -> None:
    data = {
        "id": "u-1",
        "full_name": "Alice",
        "pan": "ABCDE1234F",
        "aadhaar": "123412341234",
        "phone": "+919876543210",
        "email": "alice@example.com",
        "bank_account_number": "55555577778888",
        "ifsc_code": "HDFC0001234",
    }
    out = mask_response_dict(data)
    assert out is data  # mutated in place
    assert out["pan"] == "XXXXX1234X"
    assert out["aadhaar"] == "XXXX-XXXX-1234"
    assert out["phone"] == "+91-XXXXX-XX210"
    assert out["email"] == "a***@example.com"
    assert out["bank_account_number"].endswith("8888")
    assert out["ifsc_code"] == "HDFC0XXX234"
    # Non-PII passes through.
    assert out["id"] == "u-1"
    assert out["full_name"] == "Alice"


def test_only_specified_fields_masked_when_fields_arg_given() -> None:
    data = {"pan": "ABCDE1234F", "phone": "+919876543210"}
    mask_response_dict(data, fields=["pan"])
    assert data["pan"] == "XXXXX1234X"
    assert data["phone"] == "+919876543210"  # NOT masked


def test_nonexistent_fields_are_skipped() -> None:
    data = {"full_name": "Bob"}
    out = mask_response_dict(data, fields=["pan", "aadhaar"])
    assert out == {"full_name": "Bob"}


def test_non_string_pii_values_left_alone() -> None:
    data = {"pan": None, "email": 0, "phone": []}
    out = mask_response_dict(data)
    # Non-strings pass through — callers should always give strings.
    assert out == {"pan": None, "email": 0, "phone": []}


def test_mask_response_list_masks_every_item() -> None:
    items = [
        {"pan": "ABCDE1234F", "email": "a@example.com"},
        {"pan": "XYZAB9876Z", "email": "b@example.com"},
    ]
    out = mask_response_list(items)
    assert len(out) == 2
    for item in out:
        assert item["pan"].startswith("XXXXX")
        assert item["email"].startswith(("a***@", "b***@"))


# ---------------------------------------------------------------------------
# Permission gate.
# ---------------------------------------------------------------------------

def test_has_pii_view_true_when_present() -> None:
    assert has_pii_view({"pii.view", "voucher.post"}) is True
    assert has_pii_view(["pii.view"]) is True


def test_has_pii_view_false_when_absent_or_none() -> None:
    assert has_pii_view(None) is False
    assert has_pii_view(set()) is False
    assert has_pii_view({"voucher.post"}) is False


def test_permission_constant_is_dotted_format() -> None:
    """CLAUDE.md §8.2: permissions are `<resource>.<action>`."""
    assert PII_VIEW_PERMISSION == "pii.view"
    assert "." in PII_VIEW_PERMISSION


# ---------------------------------------------------------------------------
# Audit payload shape.
# ---------------------------------------------------------------------------

def test_audit_record_has_required_keys() -> None:
    rec = build_unmask_audit_record(
        user_id="u-123",
        organization_id="o-456",
        field_name="pan",
        record_type="customer",
        record_id="c-789",
        reason="CIBIL pull request",
    )
    assert rec["event"] == "pii_unmask"
    assert rec["user_id"] == "u-123"
    assert rec["organization_id"] == "o-456"
    assert rec["field_name"] == "pan"
    assert rec["record_type"] == "customer"
    assert rec["record_id"] == "c-789"
    assert rec["reason"] == "CIBIL pull request"


def test_audit_record_accepts_null_org_for_system_context() -> None:
    rec = build_unmask_audit_record(
        user_id="u-1",
        organization_id=None,
        field_name="email",
        record_type="user",
        record_id="u-2",
    )
    assert rec["organization_id"] is None
    assert rec["reason"] is None


# ---------------------------------------------------------------------------
# Registry completeness.
# ---------------------------------------------------------------------------

def test_every_expected_field_has_a_masker() -> None:
    expected = {
        "pan", "aadhaar", "aadhaar_number",
        "phone", "phone_number", "mobile", "mobile_number",
        "email",
        "bank_account_number", "account_number",
        "ifsc_code", "ifsc",
    }
    missing = expected - set(FIELD_MASKERS.keys())
    assert not missing, f"Missing maskers for: {missing}"
