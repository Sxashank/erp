"""Upload validation primitives for DMS (and any other user-file accept site).

CLAUDE.md §8.7:
  - Content-type allowlist (no executables, no svg-with-scripts, no random
    text/html that a user could weaponise as a phishing page).
  - Size cap (default 50 MB; adjustable per call site).
  - Filename sanitization (no path traversal, no null bytes, no control
    characters, no shell metacharacters).
  - Magic-byte sniff for high-risk types (PDFs must start with %PDF; JPEGs
    with FFD8FFE0/E1; PNGs with 89504E47; ZIPs with 504B0304).

This module does NOT run AV — ClamAV integration is deferred (STAGE-5-PENDING-001
in .stubs-approved.md).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.exceptions import BadRequestException

DEFAULT_MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


class UploadRejected(BadRequestException):
    """A user upload failed a security check."""

    def __init__(self, detail: str, error_code: str = "UPLOAD_REJECTED") -> None:
        super().__init__(detail=detail, error_code=error_code)


# ---------------------------------------------------------------------------
# Allowlist groups. Callers pick the groups relevant to the surface they
# expose. Do NOT add MIME types without a threat-model review.
# ---------------------------------------------------------------------------

DOCUMENT_MIME_TYPES: frozenset[str] = frozenset({
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "text/csv",
})

IMAGE_MIME_TYPES: frozenset[str] = frozenset({
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
})

ARCHIVE_MIME_TYPES: frozenset[str] = frozenset({
    "application/zip",
})

BANK_STATEMENT_MIME_TYPES: frozenset[str] = frozenset({
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/csv",
})

# DENY list — explicit, do not allow even if a future allowlist group adds
# them. Keep short and purposeful.
ALWAYS_DENY_MIME_TYPES: frozenset[str] = frozenset({
    "application/x-msdownload",        # .exe
    "application/x-msi",                # .msi
    "application/x-sh",                 # .sh
    "application/x-shellscript",
    "application/java-archive",        # .jar
    "application/x-executable",
    "application/x-dosexec",
    "application/x-msdos-program",
    "text/html",                        # XSS / phishing pages
    "application/xhtml+xml",
    "image/svg+xml",                    # can embed <script>
    "application/javascript",
    "text/javascript",
})


# ---------------------------------------------------------------------------
# Magic bytes — first N bytes of common file types. Used when we want a
# deeper sniff than trusting `Content-Type` (which clients can lie about).
# ---------------------------------------------------------------------------

MAGIC_BYTES: dict[str, tuple[bytes, ...]] = {
    "application/pdf": (b"%PDF-",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "application/zip": (b"PK\x03\x04",),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (b"PK\x03\x04",),
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": (b"PK\x03\x04",),
}


# ---------------------------------------------------------------------------
# Filename sanitization.
# ---------------------------------------------------------------------------

# Reject these anywhere in the filename.
_FORBIDDEN_FILENAME_RE = re.compile(r"[\x00-\x1f\x7f]|[/\\]|\.\.")
# Reject these as the entire filename (Windows reserved device names).
_RESERVED_WINDOWS_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *{f"COM{i}" for i in range(1, 10)},
    *{f"LPT{i}" for i in range(1, 10)},
}

_MAX_FILENAME_LENGTH = 255


def sanitize_filename(raw_name: str) -> str:
    """Return a safe filename or raise UploadRejected.

    Strips everything before the final path separator (defence against
    path traversal), validates no NULs / control chars, no `..`, and no
    Windows reserved device names."""
    if not raw_name:
        raise UploadRejected("Filename is empty", error_code="FILENAME_EMPTY")

    # Take only the basename component (no directory parts).
    candidate = raw_name.replace("\\", "/").split("/")[-1].strip()
    if not candidate:
        raise UploadRejected("Filename has no basename", error_code="FILENAME_EMPTY")

    if len(candidate) > _MAX_FILENAME_LENGTH:
        raise UploadRejected(
            f"Filename is too long (max {_MAX_FILENAME_LENGTH} chars)",
            error_code="FILENAME_TOO_LONG",
        )

    if _FORBIDDEN_FILENAME_RE.search(candidate):
        raise UploadRejected(
            "Filename contains forbidden characters",
            error_code="FILENAME_FORBIDDEN_CHARS",
        )

    stem = candidate.split(".")[0].upper()
    if stem in _RESERVED_WINDOWS_NAMES:
        raise UploadRejected(
            f"Filename '{candidate}' is a reserved system name",
            error_code="FILENAME_RESERVED",
        )

    return candidate


# ---------------------------------------------------------------------------
# Top-level validator.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class UploadValidationResult:
    safe_filename: str
    size_bytes: int
    content_type: str


def validate_upload(
    *,
    filename: str,
    content_type: str,
    body: bytes,
    allowed_mime_types: frozenset[str],
    max_size_bytes: int = DEFAULT_MAX_SIZE_BYTES,
    check_magic_bytes: bool = True,
) -> UploadValidationResult:
    """One-shot validation. Raises UploadRejected on any failure."""
    safe_filename = sanitize_filename(filename)

    if not content_type:
        raise UploadRejected(
            "Missing Content-Type header",
            error_code="CONTENT_TYPE_MISSING",
        )
    normalised_ct = content_type.split(";", 1)[0].strip().lower()

    if normalised_ct in ALWAYS_DENY_MIME_TYPES:
        raise UploadRejected(
            f"Content-Type '{normalised_ct}' is not permitted",
            error_code="CONTENT_TYPE_DENIED",
        )
    if normalised_ct not in allowed_mime_types:
        raise UploadRejected(
            f"Content-Type '{normalised_ct}' is not in the allowlist for this upload",
            error_code="CONTENT_TYPE_NOT_ALLOWED",
        )

    size = len(body) if body is not None else 0
    if size == 0:
        raise UploadRejected("Upload is empty", error_code="UPLOAD_EMPTY")
    if size > max_size_bytes:
        raise UploadRejected(
            f"Upload exceeds maximum size of {max_size_bytes} bytes",
            error_code="UPLOAD_TOO_LARGE",
        )

    if check_magic_bytes:
        signatures = MAGIC_BYTES.get(normalised_ct)
        if signatures is not None:
            header = body[: max(len(s) for s in signatures)]
            if not any(header.startswith(sig) for sig in signatures):
                raise UploadRejected(
                    f"File contents do not match declared type '{normalised_ct}'",
                    error_code="CONTENT_TYPE_MISMATCH",
                )

    return UploadValidationResult(
        safe_filename=safe_filename,
        size_bytes=size,
        content_type=normalised_ct,
    )
