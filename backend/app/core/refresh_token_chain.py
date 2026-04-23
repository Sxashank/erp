"""Refresh-token rotation + replay-detection helpers.

CLAUDE.md §8.1: refresh rotation on every use. When a session is rotated
(replaced by a new one in the same `token_family`), the old session is
revoked with reason = `ROTATED_REASON`. If a caller later presents a
token that maps to a session already revoked for rotation, that is
presumptive REPLAY — the entire family is compromised and every session
in it must be revoked.

This module is pure logic; the auth service imports it and wires the
DB-side effect. See `app.services.auth.auth_service.refresh_token`.

STAGE-5-PENDING-004 closure.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


ROTATED_REASON = "rotated"
REPLAY_REASON = "replay_detected"


class RefreshOutcome(str, Enum):
    """Outcome of examining a session presented on /auth/refresh."""

    VALID = "valid"                 # session is usable; proceed with rotation
    EXPIRED = "expired"             # natural expiry; reject
    ALREADY_REVOKED = "already_revoked"  # revoked for logout/manual/admin — reject
    REPLAY = "replay"               # revoked with ROTATED_REASON — PRIOR TOKEN REUSED, chain compromised


@dataclass(frozen=True)
class RefreshDecision:
    outcome: RefreshOutcome
    reason: str | None = None


class _SessionLike(Protocol):
    """Duck-type of the columns the helper inspects."""
    is_revoked: bool
    revoked_reason: str | None
    @property
    def is_valid(self) -> bool: ...


def classify_refresh(session: _SessionLike | None) -> RefreshDecision:
    """Decide what to do with a session presented on /auth/refresh.

    The caller will:
      - On VALID: rotate — revoke this session (reason=ROTATED_REASON), mint
        a new session in the same token_family, mint new access + refresh tokens.
      - On REPLAY: revoke EVERY session in the same token_family. See
        CLAUDE.md §8.1 chain-revocation rule.
      - On EXPIRED / ALREADY_REVOKED: 401 and stop.
    """
    if session is None:
        return RefreshDecision(outcome=RefreshOutcome.ALREADY_REVOKED, reason="session_not_found")

    if session.is_revoked:
        if (session.revoked_reason or "").lower() == ROTATED_REASON:
            # The token we just presented should have been replaced in the
            # last /auth/refresh. Presenting it again = replay.
            return RefreshDecision(outcome=RefreshOutcome.REPLAY)
        return RefreshDecision(
            outcome=RefreshOutcome.ALREADY_REVOKED,
            reason=session.revoked_reason,
        )

    if not session.is_valid:
        return RefreshDecision(outcome=RefreshOutcome.EXPIRED)

    return RefreshDecision(outcome=RefreshOutcome.VALID)
