"""Feature-flag tests (CLAUDE.md §6.7)."""

from __future__ import annotations

import pytest

from app.core import feature_flags
from app.core.feature_flags import (
    ALL_FLAGS,
    FeatureFlagState,
    get_flag,
    is_disabled,
    is_live,
    is_mocked,
    reset_flags,
    set_flag,
    snapshot,
)


@pytest.fixture(autouse=True)
def _clean_overrides():
    reset_flags()
    yield
    reset_flags()


# ---------------------------------------------------------------------------
# Registry invariants.
# ---------------------------------------------------------------------------

def test_every_flag_resolves_to_a_valid_state() -> None:
    for flag in ALL_FLAGS:
        state = get_flag(flag)
        assert isinstance(state, FeatureFlagState)


def test_unknown_flag_raises() -> None:
    with pytest.raises(ValueError, match="Unknown feature flag"):
        get_flag("bogus_flag")


def test_setting_unknown_flag_raises() -> None:
    with pytest.raises(ValueError):
        set_flag("bogus_flag", "on")


def test_critical_flags_are_registered() -> None:
    """If anyone deletes a vendor flag, this test surfaces it."""
    required = {
        "gstn_live",
        "ckyc_live",
        "cibil_live",
        "sms_live",
        "razorpay_live",
        "nach_live",
        "cersai_live",
        "nesl_live",
        "esign_live",
        "einvoice_live",
        "ewaybill_live",
        "clamav_scan",
        "otel_export",
    }
    missing = required - ALL_FLAGS
    assert not missing, f"Missing critical flags: {missing}"


# ---------------------------------------------------------------------------
# Resolution precedence.
# ---------------------------------------------------------------------------

def test_runtime_override_wins(monkeypatch) -> None:
    monkeypatch.setenv("FEATURE_FLAG_GSTN_LIVE", "on")
    set_flag("gstn_live", "off")
    assert get_flag("gstn_live") == FeatureFlagState.OFF


def test_env_var_overrides_defaults(monkeypatch) -> None:
    monkeypatch.setenv("FEATURE_FLAG_GSTN_LIVE", "on")
    assert get_flag("gstn_live") == FeatureFlagState.ON


def test_env_var_mock_recognized(monkeypatch) -> None:
    monkeypatch.setenv("FEATURE_FLAG_CKYC_LIVE", "mock")
    assert get_flag("ckyc_live") == FeatureFlagState.MOCK


def test_invalid_env_value_falls_back_to_default(monkeypatch) -> None:
    monkeypatch.setenv("FEATURE_FLAG_GSTN_LIVE", "not-a-valid-state")
    # Falls back to per-env default (development → MOCK).
    from app.config import settings

    if settings.APP_ENV.lower() == "production":
        assert get_flag("gstn_live") == FeatureFlagState.OFF
    else:
        assert get_flag("gstn_live") == FeatureFlagState.MOCK


def test_per_env_default_production_is_off(monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "APP_ENV", "production")
    # No env var, no override → production default is OFF.
    assert get_flag("sms_live") == FeatureFlagState.OFF


def test_per_env_default_development_is_mock(monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "APP_ENV", "development")
    assert get_flag("sms_live") == FeatureFlagState.MOCK


def test_per_env_default_test_is_mock(monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "APP_ENV", "test")
    assert get_flag("cibil_live") == FeatureFlagState.MOCK


# ---------------------------------------------------------------------------
# Sugar helpers.
# ---------------------------------------------------------------------------

def test_is_live_and_is_disabled_are_disjoint() -> None:
    set_flag("gstn_live", "on")
    assert is_live("gstn_live") is True
    assert is_mocked("gstn_live") is False
    assert is_disabled("gstn_live") is False


def test_is_mocked_true_when_mock() -> None:
    set_flag("gstn_live", "mock")
    assert is_mocked("gstn_live") is True
    assert is_live("gstn_live") is False


def test_is_disabled_true_when_off() -> None:
    set_flag("gstn_live", "off")
    assert is_disabled("gstn_live") is True


# ---------------------------------------------------------------------------
# Snapshot.
# ---------------------------------------------------------------------------

def test_snapshot_covers_every_flag() -> None:
    snap = snapshot()
    assert set(snap.keys()) == set(ALL_FLAGS)
    for v in snap.values():
        assert isinstance(v, FeatureFlagState)


def test_snapshot_is_ordered_alphabetically() -> None:
    keys = list(snapshot().keys())
    assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# No env-var leakage across tests.
# ---------------------------------------------------------------------------

def test_reset_flags_clears_runtime_overrides() -> None:
    set_flag("gstn_live", "on")
    assert get_flag("gstn_live") == FeatureFlagState.ON
    reset_flags()
    # Back to per-env default.
    from app.config import settings

    expected = (
        FeatureFlagState.OFF
        if settings.APP_ENV.lower() == "production"
        else FeatureFlagState.MOCK
    )
    assert get_flag("gstn_live") == expected
