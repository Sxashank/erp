"""Feature flags.

Gates for integration backends. A flag can be ON (real backend), OFF
(integration disabled, endpoint returns a `503 NOT_CONFIGURED`), or MOCK
(use an in-app deterministic mock — useful in dev + tests).

Precedence (highest to lowest):
  1. Explicit env var override: `FEATURE_FLAG_<NAME>=on|off|mock`.
  2. Per-environment default table below (keyed on APP_ENV).
  3. Hard-coded fallback (always MOCK in non-prod, OFF in prod).

This module is PURE — no I/O. Flags read from env on module load; tests
can override via `set_flag()` + `reset_flags()` or monkeypatch.

See CLAUDE.md §6.7 and .stubs-approved.md STAGE-6-PENDING-* entries — each
pending vendor integration has a matching flag here.
"""

from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from typing import Mapping

from app.config import settings


class FeatureFlagState(str, Enum):
    ON = "on"
    OFF = "off"
    MOCK = "mock"


# Canonical flag names. Adding a vendor integration? Add its flag here.
ALL_FLAGS: frozenset[str] = frozenset({
    # Tax
    "gstn_live",           # real GSTN portal filing
    "einvoice_live",       # real IRP e-invoice
    "ewaybill_live",       # real e-waybill portal
    "tds_traces_live",     # real TRACES filing
    # KYC / bureau
    "ckyc_live",
    "cibil_live",
    "experian_live",
    "crif_live",
    # Communication
    "sms_live",            # Msg91 or equivalent
    "email_live",          # SMTP against a real MTA (not dev sink)
    "push_live",           # FCM / APNS
    # Payment
    "razorpay_live",
    "paytm_live",
    "ccavenue_live",
    # NBFC-specific
    "nach_live",
    "cersai_live",
    "nesl_live",
    "esign_live",
    # Infra
    "clamav_scan",
    "otel_export",
})

# Per-environment defaults. Anything not listed falls back to MOCK in dev /
# staging and OFF in production — integrations ship disabled-by-default.
_DEFAULTS_BY_ENV: Mapping[str, Mapping[str, FeatureFlagState]] = {
    "production": {
        # Nothing is live-by-default in production. Ops must explicitly
        # flip via env var once credentials are rotated and audited.
    },
    "staging": {
        # Sandbox integrations may be wired in staging via env vars.
    },
    "development": {
        # Dev always gets MOCKs so laptops don't accidentally hit vendors.
    },
    "test": {
        # Tests always MOCK unless a specific test overrides.
    },
}


def _env_key(flag: str) -> str:
    return f"FEATURE_FLAG_{flag.upper()}"


def _parse_state(raw: str | None) -> FeatureFlagState | None:
    if raw is None:
        return None
    lowered = raw.strip().lower()
    try:
        return FeatureFlagState(lowered)
    except ValueError:
        return None


def _default_for_env(flag: str, env: str) -> FeatureFlagState:
    defaults = _DEFAULTS_BY_ENV.get(env.lower(), {})
    if flag in defaults:
        return defaults[flag]
    if env.lower() == "production":
        return FeatureFlagState.OFF
    return FeatureFlagState.MOCK


# ---------------------------------------------------------------------------
# Public API.
# ---------------------------------------------------------------------------

_runtime_overrides: dict[str, FeatureFlagState] = {}


def get_flag(flag: str) -> FeatureFlagState:
    """Return the current state of `flag`.

    Resolution: runtime override → env var → per-env default → hard fallback."""
    if flag not in ALL_FLAGS:
        raise ValueError(
            f"Unknown feature flag '{flag}'. Add it to ALL_FLAGS in "
            f"app.core.feature_flags."
        )
    if flag in _runtime_overrides:
        return _runtime_overrides[flag]

    env_state = _parse_state(os.environ.get(_env_key(flag)))
    if env_state is not None:
        return env_state

    return _default_for_env(flag, settings.APP_ENV)


def is_live(flag: str) -> bool:
    """Sugar: True iff the flag is ON (integration should call the real vendor)."""
    return get_flag(flag) == FeatureFlagState.ON


def is_mocked(flag: str) -> bool:
    """Sugar: True iff the flag is MOCK (use in-app deterministic mock)."""
    return get_flag(flag) == FeatureFlagState.MOCK


def is_disabled(flag: str) -> bool:
    """Sugar: True iff the flag is OFF (endpoint should return 503)."""
    return get_flag(flag) == FeatureFlagState.OFF


def set_flag(flag: str, state: FeatureFlagState | str) -> None:
    """Testing-only: set a runtime override. Use `reset_flags()` in teardown."""
    if flag not in ALL_FLAGS:
        raise ValueError(f"Unknown feature flag '{flag}'")
    if isinstance(state, str):
        parsed = _parse_state(state)
        if parsed is None:
            raise ValueError(f"Invalid state '{state}'; use on/off/mock")
        state = parsed
    _runtime_overrides[flag] = state


def reset_flags() -> None:
    """Testing-only: clear runtime overrides. Call in test teardown."""
    _runtime_overrides.clear()


def snapshot() -> dict[str, FeatureFlagState]:
    """Return the current resolved state of every flag. Useful for a
    `/admin/feature-flags` read endpoint + logging at startup."""
    return {flag: get_flag(flag) for flag in sorted(ALL_FLAGS)}
