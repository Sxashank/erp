"""Upload validation tests (CLAUDE.md §8.7)."""

from __future__ import annotations

import pytest

from app.core.upload_validation import (
    ALWAYS_DENY_MIME_TYPES,
    BANK_STATEMENT_MIME_TYPES,
    DEFAULT_MAX_SIZE_BYTES,
    DOCUMENT_MIME_TYPES,
    IMAGE_MIME_TYPES,
    UploadRejected,
    sanitize_filename,
    validate_upload,
)

PDF_HEADER = b"%PDF-1.7\n" + b"fake pdf body " * 50
PNG_HEADER = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
JPEG_HEADER = b"\xff\xd8\xff" + b"\x00" * 100
ZIP_HEADER = b"PK\x03\x04" + b"\x00" * 50


# ---------------------------------------------------------------------------
# sanitize_filename.
# ---------------------------------------------------------------------------

def test_sanitize_filename_accepts_normal_names() -> None:
    assert sanitize_filename("report.pdf") == "report.pdf"
    assert sanitize_filename("Q3-2026 summary.xlsx") == "Q3-2026 summary.xlsx"


def test_sanitize_filename_strips_directory_prefix() -> None:
    """Path traversal defence — only the basename is kept."""
    assert sanitize_filename("/etc/passwd") == "passwd"
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("C:\\Windows\\win.ini") == "win.ini"


def test_sanitize_filename_rejects_null_byte() -> None:
    with pytest.raises(UploadRejected) as exc:
        sanitize_filename("evil\x00.pdf")
    assert exc.value.error_code == "FILENAME_FORBIDDEN_CHARS"


def test_sanitize_filename_rejects_dotdot_in_name() -> None:
    with pytest.raises(UploadRejected):
        sanitize_filename("..secret.pdf")


def test_sanitize_filename_rejects_reserved_windows_names() -> None:
    for name in ["CON.txt", "PRN", "NUL.pdf", "LPT1.csv"]:
        with pytest.raises(UploadRejected) as exc:
            sanitize_filename(name)
        assert exc.value.error_code == "FILENAME_RESERVED"


def test_sanitize_filename_rejects_empty() -> None:
    with pytest.raises(UploadRejected):
        sanitize_filename("")


def test_sanitize_filename_rejects_overly_long() -> None:
    with pytest.raises(UploadRejected) as exc:
        sanitize_filename("x" * 500 + ".pdf")
    assert exc.value.error_code == "FILENAME_TOO_LONG"


# ---------------------------------------------------------------------------
# validate_upload — allowlist / deny-list.
# ---------------------------------------------------------------------------

def test_pdf_upload_accepted_in_document_group() -> None:
    result = validate_upload(
        filename="statement.pdf",
        content_type="application/pdf",
        body=PDF_HEADER,
        allowed_mime_types=DOCUMENT_MIME_TYPES,
    )
    assert result.safe_filename == "statement.pdf"
    assert result.content_type == "application/pdf"


def test_html_upload_rejected_even_if_group_forgets_to_deny() -> None:
    """HTML is in ALWAYS_DENY so even a custom allowlist with html cannot land."""
    with pytest.raises(UploadRejected) as exc:
        validate_upload(
            filename="phish.html",
            content_type="text/html",
            body=b"<html>...</html>" * 10,
            allowed_mime_types=frozenset({"text/html"} | DOCUMENT_MIME_TYPES),
        )
    assert exc.value.error_code == "CONTENT_TYPE_DENIED"


def test_svg_upload_rejected() -> None:
    with pytest.raises(UploadRejected) as exc:
        validate_upload(
            filename="logo.svg",
            content_type="image/svg+xml",
            body=b"<svg><script>alert(1)</script></svg>" * 10,
            allowed_mime_types=IMAGE_MIME_TYPES,
        )
    assert exc.value.error_code == "CONTENT_TYPE_DENIED"


def test_executable_upload_rejected() -> None:
    with pytest.raises(UploadRejected):
        validate_upload(
            filename="tool.exe",
            content_type="application/x-msdownload",
            body=b"MZ\x90\x00" + b"\x00" * 500,
            allowed_mime_types=DOCUMENT_MIME_TYPES,
        )


def test_content_type_not_in_allowlist() -> None:
    with pytest.raises(UploadRejected) as exc:
        validate_upload(
            filename="song.mp3",
            content_type="audio/mpeg",
            body=b"\x00" * 100,
            allowed_mime_types=DOCUMENT_MIME_TYPES,
        )
    assert exc.value.error_code == "CONTENT_TYPE_NOT_ALLOWED"


def test_missing_content_type_rejected() -> None:
    with pytest.raises(UploadRejected) as exc:
        validate_upload(
            filename="doc.pdf",
            content_type="",
            body=PDF_HEADER,
            allowed_mime_types=DOCUMENT_MIME_TYPES,
        )
    assert exc.value.error_code == "CONTENT_TYPE_MISSING"


# ---------------------------------------------------------------------------
# Size limits.
# ---------------------------------------------------------------------------

def test_empty_upload_rejected() -> None:
    with pytest.raises(UploadRejected) as exc:
        validate_upload(
            filename="empty.pdf",
            content_type="application/pdf",
            body=b"",
            allowed_mime_types=DOCUMENT_MIME_TYPES,
        )
    assert exc.value.error_code == "UPLOAD_EMPTY"


def test_oversize_upload_rejected() -> None:
    with pytest.raises(UploadRejected) as exc:
        validate_upload(
            filename="big.pdf",
            content_type="application/pdf",
            body=PDF_HEADER + b"\x00" * 200,
            allowed_mime_types=DOCUMENT_MIME_TYPES,
            max_size_bytes=100,
        )
    assert exc.value.error_code == "UPLOAD_TOO_LARGE"


def test_default_max_is_50mb() -> None:
    assert DEFAULT_MAX_SIZE_BYTES == 50 * 1024 * 1024


# ---------------------------------------------------------------------------
# Magic bytes / content-type spoofing.
# ---------------------------------------------------------------------------

def test_magic_bytes_mismatch_rejected_pdf() -> None:
    with pytest.raises(UploadRejected) as exc:
        validate_upload(
            filename="evil.pdf",
            content_type="application/pdf",
            body=b"<html>this is not a pdf</html>" * 10,
            allowed_mime_types=DOCUMENT_MIME_TYPES,
        )
    assert exc.value.error_code == "CONTENT_TYPE_MISMATCH"


def test_magic_bytes_match_pdf() -> None:
    result = validate_upload(
        filename="real.pdf",
        content_type="application/pdf",
        body=PDF_HEADER,
        allowed_mime_types=DOCUMENT_MIME_TYPES,
    )
    assert result.content_type == "application/pdf"


def test_magic_bytes_match_png() -> None:
    result = validate_upload(
        filename="x.png",
        content_type="image/png",
        body=PNG_HEADER,
        allowed_mime_types=IMAGE_MIME_TYPES,
    )
    assert result.content_type == "image/png"


def test_magic_bytes_match_jpeg() -> None:
    result = validate_upload(
        filename="x.jpg",
        content_type="image/jpeg",
        body=JPEG_HEADER,
        allowed_mime_types=IMAGE_MIME_TYPES,
    )
    assert result.content_type == "image/jpeg"


def test_magic_bytes_can_be_disabled() -> None:
    """Text content-types don't have a magic-byte signature; disabling the
    check lets them through without spoof detection."""
    result = validate_upload(
        filename="report.txt",
        content_type="text/plain",
        body=b"plain text report body",
        allowed_mime_types=DOCUMENT_MIME_TYPES,
        check_magic_bytes=False,
    )
    assert result.content_type == "text/plain"


def test_content_type_charset_parameter_is_stripped() -> None:
    """`text/plain; charset=utf-8` normalises to `text/plain` for allowlist."""
    result = validate_upload(
        filename="notes.txt",
        content_type="text/plain; charset=utf-8",
        body=b"hello",
        allowed_mime_types=DOCUMENT_MIME_TYPES,
    )
    assert result.content_type == "text/plain"


# ---------------------------------------------------------------------------
# Group sanity — ensure deny list is disjoint from allow groups.
# ---------------------------------------------------------------------------

def test_deny_list_is_disjoint_from_every_allow_group() -> None:
    for group in (DOCUMENT_MIME_TYPES, IMAGE_MIME_TYPES, BANK_STATEMENT_MIME_TYPES):
        assert group.isdisjoint(ALWAYS_DENY_MIME_TYPES), (
            f"deny list must not overlap with {group}"
        )
