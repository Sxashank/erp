"""Antivirus scan tests (STAGE-5-PENDING-001 closure).

Covers the three feature-flag modes (OFF / MOCK / ON) and the two high-level
APIs (`scan_upload` returns a result; `enforce_scan` raises on detection).

We don't exercise a real ClamAV sidecar in unit tests — that's an integration
concern. For the MOCK path we hit the real in-app mock with the EICAR pattern.
For the ON path we patch the ClamAV backend to simulate both success and a
connection failure.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.av_scan import (
    EICAR_TEST_STRING,
    AVUnavailable,
    ScanResult,
    ScanVerdict,
    VirusFound,
    enforce_scan,
    scan_upload,
)
from app.core.feature_flags import FeatureFlagState, reset_flags, set_flag


@pytest.fixture(autouse=True)
def _reset_flags():
    """Every test starts with a clean flag state."""
    reset_flags()
    yield
    reset_flags()


# ---------------------------------------------------------------------------
# OFF: no scan performed.
# ---------------------------------------------------------------------------


def test_flag_off_returns_noop_clean_without_invoking_scanner() -> None:
    """OFF → verdict=CLEAN, backend="noop" even for EICAR content.

    This is the production default until the sidecar is deployed. It's
    intentional: fresh deploys must not break uploads before ClamAV is up.
    """
    set_flag("clamav_scan", FeatureFlagState.OFF)
    result = scan_upload(EICAR_TEST_STRING)
    assert result == ScanResult(verdict=ScanVerdict.CLEAN, signature=None, backend="noop")


def test_enforce_scan_off_does_not_raise_even_for_eicar() -> None:
    set_flag("clamav_scan", FeatureFlagState.OFF)
    # Does not raise — noop is by design.
    enforce_scan(EICAR_TEST_STRING)


# ---------------------------------------------------------------------------
# MOCK: in-app scanner, EICAR recognised.
# ---------------------------------------------------------------------------


def test_flag_mock_flags_eicar_as_infected() -> None:
    set_flag("clamav_scan", FeatureFlagState.MOCK)
    result = scan_upload(EICAR_TEST_STRING)
    assert result.verdict is ScanVerdict.INFECTED
    assert result.signature == "Eicar-Test-Signature"
    assert result.backend == "mock"


def test_flag_mock_allows_benign_payload() -> None:
    set_flag("clamav_scan", FeatureFlagState.MOCK)
    result = scan_upload(b"hello world" * 100)
    assert result.verdict is ScanVerdict.CLEAN
    assert result.backend == "mock"


def test_enforce_scan_mock_raises_on_eicar() -> None:
    set_flag("clamav_scan", FeatureFlagState.MOCK)
    with pytest.raises(VirusFound) as exc:
        enforce_scan(EICAR_TEST_STRING)
    assert exc.value.signature == "Eicar-Test-Signature"
    assert exc.value.error_code == "UPLOAD_INFECTED"


def test_enforce_scan_mock_returns_clean_result_on_benign() -> None:
    set_flag("clamav_scan", FeatureFlagState.MOCK)
    result = enforce_scan(b"clean content")
    assert result.verdict is ScanVerdict.CLEAN


def test_mock_flags_eicar_wrapped_in_larger_buffer() -> None:
    """The EICAR pattern buried in a larger payload should still be caught.

    Real AV engines scan the whole stream; our mock likewise substring-matches.
    Regression guard against someone tightening the mock to startswith().
    """
    set_flag("clamav_scan", FeatureFlagState.MOCK)
    payload = b"HEADER\r\n\r\n" + EICAR_TEST_STRING + b"\r\nFOOTER"
    result = scan_upload(payload)
    assert result.verdict is ScanVerdict.INFECTED


# ---------------------------------------------------------------------------
# ON: real ClamAV backend (patched at the function boundary).
# ---------------------------------------------------------------------------


def test_flag_on_dispatches_to_clamav_backend() -> None:
    """ON → scan_upload calls the _scan_clamav branch."""
    set_flag("clamav_scan", FeatureFlagState.ON)
    fake_result = ScanResult(verdict=ScanVerdict.CLEAN, signature=None, backend="clamav")
    with patch("app.core.av_scan._scan_clamav", return_value=fake_result) as mock:
        result = scan_upload(b"payload")
    assert mock.called
    assert result is fake_result


def test_flag_on_propagates_infected_finding_via_enforce_scan() -> None:
    set_flag("clamav_scan", FeatureFlagState.ON)
    fake_result = ScanResult(
        verdict=ScanVerdict.INFECTED,
        signature="Win.Virus.Test-1",
        backend="clamav",
    )
    with patch("app.core.av_scan._scan_clamav", return_value=fake_result):
        with pytest.raises(VirusFound) as exc:
            enforce_scan(b"payload")
    assert exc.value.signature == "Win.Virus.Test-1"


def test_flag_on_surfaces_unavailable_not_as_virus_finding() -> None:
    """AV sidecar down → AVUnavailable, NOT VirusFound.

    This is critical: an operator downtime must NEVER be mistaken for a virus
    detection (silent accept or silent reject are both wrong). The caller
    turns this into a 503 the user can retry.
    """
    set_flag("clamav_scan", FeatureFlagState.ON)
    with patch(
        "app.core.av_scan._scan_clamav",
        side_effect=AVUnavailable("ClamAV unreachable: [Errno 61] Connection refused"),
    ):
        with pytest.raises(AVUnavailable):
            enforce_scan(b"payload")
        # Also via scan_upload — not swallowed.
        with pytest.raises(AVUnavailable):
            scan_upload(b"payload")


def test_flag_on_error_verdict_is_surfaced_not_rewritten() -> None:
    """verdict=ERROR from the backend must reach the caller unchanged.

    A clamd response we can't parse (e.g. protocol drift) is not a virus
    finding and not a connection failure — we want the ERROR verdict +
    signature=None so the caller logs it and decides.
    """
    set_flag("clamav_scan", FeatureFlagState.ON)
    fake = ScanResult(
        verdict=ScanVerdict.ERROR,
        signature=None,
        backend="clamav",
        error="Unexpected clamd reply: {'stream': ('XX',)}",
    )
    with patch("app.core.av_scan._scan_clamav", return_value=fake):
        result = scan_upload(b"payload")
        # enforce_scan does NOT raise on ERROR — that's the caller's call.
        result_enforce = enforce_scan(b"payload")
    assert result.verdict is ScanVerdict.ERROR
    assert result.error is not None
    assert result_enforce.verdict is ScanVerdict.ERROR


# ---------------------------------------------------------------------------
# Exception carries the error code expected by the DMS endpoint.
# ---------------------------------------------------------------------------


def test_virus_found_exception_carries_error_code() -> None:
    """Frontend relies on error_code=UPLOAD_INFECTED to show the right toast.

    Regression guard against someone renaming the code.
    """
    exc = VirusFound(signature="Trojan.X")
    assert exc.signature == "Trojan.X"
    assert exc.error_code == "UPLOAD_INFECTED"
    assert "Trojan.X" in str(exc)
