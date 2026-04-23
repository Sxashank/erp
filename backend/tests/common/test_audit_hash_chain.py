"""Audit integrity hash chain tests (CLAUDE.md §8.5)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.audit_hash_chain import (
    GENESIS_ANCHOR,
    build_chain,
    canonicalise_row,
    compute_day_anchor,
    verify_chain,
)


SAMPLE_ROW_1 = {
    "id": "a-1",
    "created_at": datetime(2026, 4, 22, 10, 0, 0, tzinfo=timezone.utc),
    "user_id": "u-1",
    "action": "VOUCHER_CREATE",
    "resource_id": "v-1",
    "extra": None,
}
SAMPLE_ROW_2 = {
    "id": "a-2",
    "created_at": datetime(2026, 4, 22, 11, 30, 0, tzinfo=timezone.utc),
    "user_id": "u-1",
    "action": "VOUCHER_POST",
    "resource_id": "v-1",
    "extra": None,
}


# ---------------------------------------------------------------------------
# Canonicalisation.
# ---------------------------------------------------------------------------

def test_canonical_rendering_is_alphabetical_by_key() -> None:
    s = canonicalise_row({"b": 1, "a": 2, "c": 3})
    assert s == "a=2|b=1|c=3"


def test_canonical_rendering_of_none_is_null() -> None:
    s = canonicalise_row({"x": None})
    assert s == "x=null"


def test_canonical_rendering_of_datetime_is_isoformat_with_tz() -> None:
    dt = datetime(2026, 4, 22, 10, 0, 0, tzinfo=timezone.utc)
    s = canonicalise_row({"t": dt})
    assert "2026-04-22T10:00:00+00:00" in s


def test_canonical_rendering_fills_tz_if_missing() -> None:
    dt = datetime(2026, 4, 22, 10, 0, 0)  # naive
    s = canonicalise_row({"t": dt})
    assert "+00:00" in s


def test_canonical_rendering_stable_across_dict_ordering() -> None:
    """Inserting keys in different orders must give the same canonical form."""
    a = canonicalise_row({"a": 1, "b": 2})
    b = canonicalise_row({"b": 2, "a": 1})
    assert a == b


# ---------------------------------------------------------------------------
# Day-anchor hash.
# ---------------------------------------------------------------------------

def test_anchor_with_no_rows_depends_only_on_previous_anchor() -> None:
    a = compute_day_anchor(rows=[], previous_anchor=GENESIS_ANCHOR)
    b = compute_day_anchor(rows=[], previous_anchor=GENESIS_ANCHOR)
    assert a == b
    # Different seed → different anchor.
    c = compute_day_anchor(rows=[], previous_anchor="ff" * 32)
    assert c != a


def test_anchor_is_deterministic() -> None:
    a = compute_day_anchor(rows=[SAMPLE_ROW_1, SAMPLE_ROW_2])
    b = compute_day_anchor(rows=[SAMPLE_ROW_1, SAMPLE_ROW_2])
    assert a == b


def test_anchor_changes_when_any_row_changes() -> None:
    original = compute_day_anchor(rows=[SAMPLE_ROW_1, SAMPLE_ROW_2])
    tampered_row = {**SAMPLE_ROW_2, "action": "VOUCHER_DELETE"}
    tampered = compute_day_anchor(rows=[SAMPLE_ROW_1, tampered_row])
    assert original != tampered


def test_anchor_changes_when_rows_reordered() -> None:
    """Rows are canonical at the row level but the DAY bucket preserves
    order as provided — callers must sort by (created_at, id) themselves.
    This test documents that ordering matters at the day level."""
    a = compute_day_anchor(rows=[SAMPLE_ROW_1, SAMPLE_ROW_2])
    b = compute_day_anchor(rows=[SAMPLE_ROW_2, SAMPLE_ROW_1])
    assert a != b


def test_anchor_is_64_hex_chars() -> None:
    a = compute_day_anchor(rows=[SAMPLE_ROW_1])
    assert len(a) == 64
    int(a, 16)  # parseable as hex


# ---------------------------------------------------------------------------
# Chain building + verification.
# ---------------------------------------------------------------------------

def test_build_chain_rolls_anchor_across_days() -> None:
    rows_by_day = {
        "2026-04-22": [SAMPLE_ROW_1, SAMPLE_ROW_2],
        "2026-04-23": [SAMPLE_ROW_1],
    }
    chain = build_chain(rows_by_day=rows_by_day)
    assert len(chain) == 2
    assert chain[0].previous_anchor == GENESIS_ANCHOR
    assert chain[1].previous_anchor == chain[0].anchor
    assert chain[0].row_count == 2
    assert chain[1].row_count == 1


def test_verify_chain_returns_empty_on_intact() -> None:
    rows_by_day = {
        "2026-04-22": [SAMPLE_ROW_1, SAMPLE_ROW_2],
        "2026-04-23": [SAMPLE_ROW_1],
    }
    chain = build_chain(rows_by_day=rows_by_day)
    expected = {r.day: r.anchor for r in chain}
    mismatches = verify_chain(rows_by_day=rows_by_day, expected_anchors=expected)
    assert mismatches == []


def test_verify_chain_detects_day_2_tamper() -> None:
    """Tampering with a row on day 1 must surface a mismatch on BOTH day 1
    and day 2 (propagation)."""
    rows_by_day = {
        "2026-04-22": [SAMPLE_ROW_1, SAMPLE_ROW_2],
        "2026-04-23": [SAMPLE_ROW_1],
    }
    original = build_chain(rows_by_day=rows_by_day)
    expected = {r.day: r.anchor for r in original}

    # Tamper with day 1.
    tampered = {
        "2026-04-22": [SAMPLE_ROW_1, {**SAMPLE_ROW_2, "action": "VOUCHER_DELETE"}],
        "2026-04-23": [SAMPLE_ROW_1],
    }
    mismatches = verify_chain(rows_by_day=tampered, expected_anchors=expected)

    # Both days must mismatch.
    assert mismatches == ["2026-04-22", "2026-04-23"]


def test_verify_chain_detects_day_2_only_when_day_2_tampered() -> None:
    rows_by_day = {
        "2026-04-22": [SAMPLE_ROW_1],
        "2026-04-23": [SAMPLE_ROW_2],
    }
    original = build_chain(rows_by_day=rows_by_day)
    expected = {r.day: r.anchor for r in original}

    tampered = {
        "2026-04-22": [SAMPLE_ROW_1],
        "2026-04-23": [{**SAMPLE_ROW_2, "action": "VOUCHER_DELETE"}],
    }
    mismatches = verify_chain(rows_by_day=tampered, expected_anchors=expected)
    assert mismatches == ["2026-04-23"]


def test_verify_chain_detects_inserted_row() -> None:
    """Inserting a fake audit row in the middle of a day changes the
    anchor — the tamper surfaces even without deleting anything."""
    rows_by_day = {
        "2026-04-22": [SAMPLE_ROW_1],
    }
    original = build_chain(rows_by_day=rows_by_day)
    expected = {r.day: r.anchor for r in original}

    tampered = {
        "2026-04-22": [SAMPLE_ROW_1, {**SAMPLE_ROW_2, "id": "planted"}],
    }
    mismatches = verify_chain(rows_by_day=tampered, expected_anchors=expected)
    assert mismatches == ["2026-04-22"]


def test_genesis_anchor_is_all_zeros() -> None:
    assert GENESIS_ANCHOR == "0" * 64
