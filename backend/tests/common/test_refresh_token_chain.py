"""Refresh-token rotation + replay-detection tests (STAGE-5-PENDING-004)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.core.refresh_token_chain import (
    REPLAY_REASON,
    ROTATED_REASON,
    RefreshOutcome,
    classify_refresh,
)


@dataclass
class _FakeSession:
    is_revoked: bool = False
    revoked_reason: str | None = None
    _valid: bool = True

    @property
    def is_valid(self) -> bool:
        return self._valid and not self.is_revoked


def test_none_session_is_already_revoked() -> None:
    d = classify_refresh(None)
    assert d.outcome == RefreshOutcome.ALREADY_REVOKED
    assert d.reason == "session_not_found"


def test_fresh_session_is_valid() -> None:
    d = classify_refresh(_FakeSession())
    assert d.outcome == RefreshOutcome.VALID


def test_expired_session_is_expired() -> None:
    d = classify_refresh(_FakeSession(_valid=False))
    assert d.outcome == RefreshOutcome.EXPIRED


def test_manually_revoked_session_is_revoked() -> None:
    s = _FakeSession(is_revoked=True, revoked_reason="logout")
    d = classify_refresh(s)
    assert d.outcome == RefreshOutcome.ALREADY_REVOKED
    assert d.reason == "logout"


def test_admin_revoked_session_is_revoked() -> None:
    s = _FakeSession(is_revoked=True, revoked_reason="admin")
    d = classify_refresh(s)
    assert d.outcome == RefreshOutcome.ALREADY_REVOKED


def test_rotated_session_presented_again_is_replay() -> None:
    """Core invariant: a session that was rotated (consumed) must not be
    accepted a second time — it's a stolen-token replay."""
    s = _FakeSession(is_revoked=True, revoked_reason=ROTATED_REASON)
    d = classify_refresh(s)
    assert d.outcome == RefreshOutcome.REPLAY


def test_rotated_reason_is_case_insensitive() -> None:
    s = _FakeSession(is_revoked=True, revoked_reason="ROTATED")
    d = classify_refresh(s)
    assert d.outcome == RefreshOutcome.REPLAY


def test_reasons_surface_constants() -> None:
    assert ROTATED_REASON == "rotated"
    assert REPLAY_REASON == "replay_detected"
