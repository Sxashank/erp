"""Antivirus-scan abstraction for DMS uploads (STAGE-5-PENDING-001 closure).

CLAUDE.md §8.7 requires every DMS upload to pass an AV check before it
lands in storage. The concrete backend is ClamAV via the ``clamd`` TCP/UNIX
protocol; this module presents a narrow, synchronous interface that plays
nicely with async callers (via ``run_in_threadpool`` inside the DMS
service).

Three modes, selected by the ``clamav_scan`` feature flag:

  * **ON**  — talk to a ClamAV sidecar (configured by ``CLAMAV_HOST`` /
    ``CLAMAV_PORT`` env vars) and raise ``VirusFound`` on detection.
  * **MOCK** — deterministic in-app scanner that flags the EICAR test
    pattern and lets everything else through. Used in dev and tests.
  * **OFF** — scan is a no-op. This is the default in ``production``
    (flag must be flipped explicitly once the sidecar is deployed) so
    fresh deploys without ClamAV still work. Auditors will flip it ON.

The module is pure Python and does NOT import ``clamd`` at module load —
``clamd`` is imported lazily so projects without the dependency can still
run tests that use MOCK mode.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Final

from app.core.feature_flags import FeatureFlagState, get_flag

# The EICAR test file — a harmless 68-byte string the industry uses to
# prove AV engines are actually scanning content. Any non-toy scanner
# recognises it as a virus.
EICAR_TEST_STRING: Final[bytes] = (
    b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
)


class ScanVerdict(str, Enum):
    CLEAN = "CLEAN"
    INFECTED = "INFECTED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ScanResult:
    verdict: ScanVerdict
    signature: str | None  # virus name on INFECTED, None on CLEAN
    backend: str  # "clamav" / "mock" / "noop"
    error: str | None = None  # non-None only when verdict = ERROR


class VirusFound(Exception):
    """Raised when a scanner reports an infected payload.

    Carries the signature string so the DMS audit row can log which virus
    was detected — support engineers need that to triage.
    """

    def __init__(self, signature: str) -> None:
        super().__init__(f"Upload rejected by antivirus: {signature}")
        self.signature = signature
        self.error_code = "UPLOAD_INFECTED"


class AVUnavailable(Exception):
    """Raised when the flag says ON but we couldn't reach the scanner.

    This is NOT a virus finding — it means the ClamAV sidecar is down or
    misconfigured. Callers should surface this as a 503 so that operators
    notice and the user can retry, rather than silently accepting the file.
    """


# ---------------------------------------------------------------------------
# Mock backend.
# ---------------------------------------------------------------------------


def _scan_mock(body: bytes) -> ScanResult:
    """Deterministic in-app scanner used in dev/test.

    Only the EICAR signature is flagged — everything else comes back clean.
    That's enough to exercise the "infected → VirusFound" code path without
    needing a real AV sidecar running in CI.
    """
    if EICAR_TEST_STRING in body:
        return ScanResult(
            verdict=ScanVerdict.INFECTED,
            signature="Eicar-Test-Signature",
            backend="mock",
        )
    return ScanResult(verdict=ScanVerdict.CLEAN, signature=None, backend="mock")


# ---------------------------------------------------------------------------
# ClamAV backend — imports `clamd` lazily.
# ---------------------------------------------------------------------------


def _scan_clamav(body: bytes) -> ScanResult:
    """Talk to the ClamAV sidecar via ``clamd``.

    Connection details:
      * Host defaults to ``CLAMAV_HOST`` env var, else ``clamav``
        (the docker-compose service name).
      * Port defaults to ``CLAMAV_PORT``, else 3310 (clamd default).

    Failure modes distinguished:
      * Connection failure / timeout → ``AVUnavailable`` (503 territory).
      * Engine result ``FOUND`` → ``ScanResult(verdict=INFECTED, signature=...)``.
      * Engine result ``OK`` → ``ScanResult(verdict=CLEAN, ...)``.
      * Anything else → ``ScanResult(verdict=ERROR, ...)`` — caller decides.
    """
    try:
        import clamd  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover — deploy-time issue
        raise AVUnavailable("clamd library is not installed") from exc

    host = os.getenv("CLAMAV_HOST", "clamav")
    port = int(os.getenv("CLAMAV_PORT", "3310"))
    try:
        cd = clamd.ClamdNetworkSocket(host=host, port=port, timeout=10)
        # instream reads a file-like; wrap bytes in BytesIO.
        from io import BytesIO

        result = cd.instream(BytesIO(body))
    except Exception as exc:  # clamd raises a zoo of exceptions; funnel them
        raise AVUnavailable(f"ClamAV unreachable: {exc}") from exc

    # clamd returns {"stream": ("OK"|"FOUND"|..., signature)}.
    stream_result = result.get("stream") if isinstance(result, dict) else None
    if not stream_result:
        return ScanResult(
            verdict=ScanVerdict.ERROR,
            signature=None,
            backend="clamav",
            error=f"Unexpected clamd reply: {result!r}",
        )

    status, signature = stream_result[0], stream_result[1] if len(stream_result) > 1 else None
    if status == "OK":
        return ScanResult(verdict=ScanVerdict.CLEAN, signature=None, backend="clamav")
    if status == "FOUND":
        return ScanResult(
            verdict=ScanVerdict.INFECTED,
            signature=signature or "Unknown",
            backend="clamav",
        )
    return ScanResult(
        verdict=ScanVerdict.ERROR,
        signature=None,
        backend="clamav",
        error=f"ClamAV status: {status}",
    )


# ---------------------------------------------------------------------------
# Dispatcher — wired to the feature flag.
# ---------------------------------------------------------------------------


def scan_upload(body: bytes) -> ScanResult:
    """Scan a file body. The concrete backend depends on the ``clamav_scan`` flag.

    Does NOT raise on INFECTED — returns the result so the caller can decide
    whether to reject the upload (the standard path is to raise
    :class:`VirusFound`) or log-and-continue (quarantine workflow). Raises
    :class:`AVUnavailable` only when the scanner itself is unreachable.
    """
    state = get_flag("clamav_scan")
    if state is FeatureFlagState.OFF:
        return ScanResult(verdict=ScanVerdict.CLEAN, signature=None, backend="noop")
    if state is FeatureFlagState.MOCK:
        return _scan_mock(body)
    return _scan_clamav(body)


def enforce_scan(body: bytes) -> ScanResult:
    """Scan + raise :class:`VirusFound` on detection.

    The canonical entry point for upload paths that should refuse infected
    content outright. Returns the scan result on CLEAN so the caller can
    stamp ``av_scanned_at`` / ``av_engine`` / ``av_signature=None`` on the
    document row.
    """
    result = scan_upload(body)
    if result.verdict is ScanVerdict.INFECTED:
        raise VirusFound(result.signature or "Unknown")
    return result
