"""Unit tests for idempotency helpers.

We test the pure functions here; the middleware is exercised end-to-end in
backend/tests/integration/test_idempotency_flow.py.

See CLAUDE.md §6.3.
"""

from __future__ import annotations

import json

import pytest

from app.middleware.idempotency import (
    MUTATING_METHODS,
    MUTATING_RESOURCES,
    _hash_body,
    _requires_idempotency,
)


class _FakeRequest:
    def __init__(self, method: str, path: str) -> None:
        self.method = method

        class _URL:
            def __init__(self, p: str) -> None:
                self.path = p

        self.url = _URL(path)


@pytest.mark.parametrize(
    "method,path,expected",
    [
        ("POST", "/api/v1/vouchers", True),
        ("POST", "/api/v1/vouchers/abc-123/submit", True),
        ("PUT", "/api/v1/payments/x-y-z", True),
        ("DELETE", "/api/v1/payments/x-y-z", True),
        ("GET", "/api/v1/vouchers", False),
        ("POST", "/api/v1/organizations", False),
        ("POST", "/api/v1/auth/login", False),
        ("POST", "/api/v1/voucherss", False),  # near-miss resource
        ("POST", "/api/v1/", False),
    ],
)
def test_requires_idempotency(method: str, path: str, expected: bool) -> None:
    assert _requires_idempotency(_FakeRequest(method, path)) is expected


def test_mutating_resources_covers_major_financial_surfaces() -> None:
    # A sanity check that we didn't shrink the list accidentally.
    for required in ("vouchers", "payments", "receipts", "disbursements", "payroll"):
        assert required in MUTATING_RESOURCES, f"{required} must be in MUTATING_RESOURCES"


def test_mutating_methods_set() -> None:
    assert MUTATING_METHODS == {"POST", "PUT", "PATCH", "DELETE"}


def test_hash_body_deterministic_for_equivalent_json() -> None:
    a = json.dumps({"amount": 100, "account": "x"}).encode()
    b = json.dumps({"account": "x", "amount": 100}, separators=(",", ": ")).encode()
    # Different serializations of equivalent JSON → same hash.
    assert _hash_body(a) == _hash_body(b)


def test_hash_body_differs_for_different_payload() -> None:
    a = json.dumps({"amount": 100}).encode()
    b = json.dumps({"amount": 101}).encode()
    assert _hash_body(a) != _hash_body(b)


def test_hash_body_handles_non_json() -> None:
    raw = b"not-json-payload"
    # Should not raise; should produce a hex digest.
    digest = _hash_body(raw)
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_hash_body_empty_input_is_zero_hash() -> None:
    import hashlib

    assert _hash_body(b"") == hashlib.sha256(b"").hexdigest()
