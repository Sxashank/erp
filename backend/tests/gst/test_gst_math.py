"""GST math golden tests (STAGE-4-PENDING-006 closure).

Portal-free computation: CGST/SGST/IGST split, RCM applicability, blocked
ITC, and GSTR-2B matching. See CLAUDE.md §4.5 / §7.1.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.core.gst_math import (
    BLOCKED_ITC_CATEGORIES,
    GSTInvoiceKey,
    NOTIFIED_RCM_HSN_CODES,
    RCM_DAILY_THRESHOLD,
    compute_gst,
    is_itc_blocked,
    is_rcm_applicable,
    match_gstr_2b,
)


# ---------------------------------------------------------------------------
# CGST + SGST split for intra-state.
# ---------------------------------------------------------------------------

def test_intra_state_18pct_splits_to_9_9() -> None:
    b = compute_gst(
        taxable_value=Decimal("10000.00"),
        gst_rate_pct=Decimal("18"),
        is_interstate=False,
    )
    assert b.cgst_amount == Decimal("900.00")
    assert b.sgst_amount == Decimal("900.00")
    assert b.igst_amount == Decimal("0")
    assert b.total_tax == Decimal("1800.00")
    assert b.total_invoice_value == Decimal("11800.00")


def test_intra_state_5pct_splits_to_2_5_2_5() -> None:
    b = compute_gst(
        taxable_value=Decimal("10000.00"),
        gst_rate_pct=Decimal("5"),
        is_interstate=False,
    )
    assert b.cgst_amount == Decimal("250.00")
    assert b.sgst_amount == Decimal("250.00")
    assert b.total_tax == Decimal("500.00")


def test_intra_state_28pct_with_cess_15pct() -> None:
    """Luxury vehicle at 28% + 15% cess."""
    b = compute_gst(
        taxable_value=Decimal("1000000.00"),
        gst_rate_pct=Decimal("28"),
        is_interstate=False,
        cess_rate_pct=Decimal("15"),
    )
    assert b.cgst_amount == Decimal("140000.00")
    assert b.sgst_amount == Decimal("140000.00")
    assert b.igst_amount == Decimal("0")
    assert b.cess_amount == Decimal("150000.00")
    assert b.total_tax == Decimal("430000.00")
    assert b.total_invoice_value == Decimal("1430000.00")


# ---------------------------------------------------------------------------
# IGST for inter-state.
# ---------------------------------------------------------------------------

def test_inter_state_18pct_is_full_igst() -> None:
    b = compute_gst(
        taxable_value=Decimal("10000.00"),
        gst_rate_pct=Decimal("18"),
        is_interstate=True,
    )
    assert b.cgst_amount == Decimal("0")
    assert b.sgst_amount == Decimal("0")
    assert b.igst_amount == Decimal("1800.00")
    assert b.total_tax == Decimal("1800.00")


def test_inter_state_does_not_double_count() -> None:
    """Inter + intra totals must be identical."""
    intra = compute_gst(
        taxable_value=Decimal("50000"),
        gst_rate_pct=Decimal("12"),
        is_interstate=False,
    )
    inter = compute_gst(
        taxable_value=Decimal("50000"),
        gst_rate_pct=Decimal("12"),
        is_interstate=True,
    )
    assert intra.total_tax == inter.total_tax


# ---------------------------------------------------------------------------
# Edge cases + validation.
# ---------------------------------------------------------------------------

def test_zero_rate_yields_zero_tax() -> None:
    b = compute_gst(
        taxable_value=Decimal("10000"),
        gst_rate_pct=Decimal("0"),
        is_interstate=False,
    )
    assert b.total_tax == Decimal("0")
    assert b.total_invoice_value == Decimal("10000")


def test_zero_taxable_value_yields_zero() -> None:
    b = compute_gst(
        taxable_value=Decimal("0"),
        gst_rate_pct=Decimal("18"),
        is_interstate=False,
    )
    assert b.total_tax == Decimal("0")
    assert b.total_invoice_value == Decimal("0")


@pytest.mark.parametrize("bad", [Decimal("-1"), Decimal("-1000.50")])
def test_negative_taxable_value_rejected(bad: Decimal) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        compute_gst(taxable_value=bad, gst_rate_pct=Decimal("18"), is_interstate=False)


def test_negative_rate_rejected() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        compute_gst(
            taxable_value=Decimal("100"),
            gst_rate_pct=Decimal("-1"),
            is_interstate=False,
        )


def test_output_is_rounded_to_two_decimals() -> None:
    b = compute_gst(
        taxable_value=Decimal("333.33"),
        gst_rate_pct=Decimal("18"),
        is_interstate=False,
    )
    assert b.cgst_amount.as_tuple().exponent == -2
    assert b.sgst_amount.as_tuple().exponent == -2


def test_half_rate_rounding_is_symmetric() -> None:
    """CGST + SGST sum to within ±₹0.01 of what a single 18% would produce."""
    for taxable in ("333.33", "777.77", "9999.99", "12345.67"):
        t = Decimal(taxable)
        b = compute_gst(taxable_value=t, gst_rate_pct=Decimal("18"), is_interstate=False)
        full = compute_gst(taxable_value=t, gst_rate_pct=Decimal("18"), is_interstate=True)
        assert abs((b.cgst_amount + b.sgst_amount) - full.igst_amount) <= Decimal("0.01")


# ---------------------------------------------------------------------------
# RCM applicability.
# ---------------------------------------------------------------------------

def test_rcm_false_for_registered_vendor_normal_supply() -> None:
    assert (
        is_rcm_applicable(
            vendor_is_registered=True,
            hsn_code="996311",  # not in notified list
        )
        is False
    )


def test_rcm_true_for_notified_hsn_even_if_vendor_registered() -> None:
    """Legal services by advocate → RCM regardless of vendor registration."""
    assert (
        is_rcm_applicable(
            vendor_is_registered=True,
            hsn_code="998212",
        )
        is True
    )


def test_rcm_true_for_gta_services() -> None:
    assert (
        is_rcm_applicable(
            vendor_is_registered=True,
            hsn_code="996511",
        )
        is True
    )


def test_rcm_true_for_imports() -> None:
    assert is_rcm_applicable(vendor_is_registered=True, is_import=True) is True


def test_rcm_true_for_unregistered_above_5k_daily() -> None:
    assert (
        is_rcm_applicable(
            vendor_is_registered=False,
            today_aggregate_from_vendor=Decimal("6000"),
        )
        is True
    )


def test_rcm_false_for_unregistered_at_or_below_5k_daily() -> None:
    assert (
        is_rcm_applicable(
            vendor_is_registered=False,
            today_aggregate_from_vendor=Decimal("5000"),
        )
        is False
    )
    assert (
        is_rcm_applicable(
            vendor_is_registered=False,
            today_aggregate_from_vendor=Decimal("1"),
        )
        is False
    )


def test_rcm_threshold_constant() -> None:
    """RBI notification is ₹5000/day; encoded as a constant so we can migrate
    if the ceiling moves."""
    assert RCM_DAILY_THRESHOLD == Decimal("5000")


def test_notified_rcm_hsn_list_includes_standard_entries() -> None:
    for expected in ("996511", "996512", "998212", "998213", "998595", "998559"):
        assert expected in NOTIFIED_RCM_HSN_CODES


# ---------------------------------------------------------------------------
# Blocked credits.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "category",
    [
        "MOTOR_VEHICLE",
        "motor_vehicle",            # case-insensitive
        "FOOD_AND_BEVERAGES",
        "CLUB_MEMBERSHIP",
        "WORKS_CONTRACT_IMMOVABLE",
        "PERSONAL_CONSUMPTION",
    ],
)
def test_itc_blocked_for_17_5_categories(category: str) -> None:
    assert is_itc_blocked(category) is True


@pytest.mark.parametrize("category", ["OFFICE_STATIONERY", "PROFESSIONAL_FEES", "RENT_COMMERCIAL"])
def test_itc_allowed_for_normal_business_expenses(category: str) -> None:
    assert is_itc_blocked(category) is False


def test_itc_blocked_handles_none_and_empty() -> None:
    assert is_itc_blocked(None) is False
    assert is_itc_blocked("") is False


def test_blocked_list_contains_all_17_5_categories() -> None:
    """Don't silently shrink this list — it's the statutory block list."""
    required = {
        "MOTOR_VEHICLE",
        "FOOD_AND_BEVERAGES",
        "OUTDOOR_CATERING",
        "BEAUTY_TREATMENT",
        "HEALTH_SERVICES",
        "CLUB_MEMBERSHIP",
        "LIFE_INSURANCE",
        "HEALTH_INSURANCE",
        "TRAVEL_BENEFITS",
        "WORKS_CONTRACT_IMMOVABLE",
        "CONSTRUCTION_IMMOVABLE",
        "PERSONAL_CONSUMPTION",
        "LOST_DESTROYED_GIFTS",
    }
    missing = required - BLOCKED_ITC_CATEGORIES
    assert not missing, f"Missing blocked-ITC categories: {missing}"


# ---------------------------------------------------------------------------
# GSTR-2B matching.
# ---------------------------------------------------------------------------

def _key(gstin: str, num: str, day: str = "2026-04-10") -> GSTInvoiceKey:
    return GSTInvoiceKey(gstin_supplier=gstin, invoice_number=num, invoice_date=day)


def test_match_all_identical_produces_matched() -> None:
    books = {_key("27AAAA0000A1Z5", "INV001"): Decimal("1180.00")}
    portal = {_key("27AAAA0000A1Z5", "INV001"): Decimal("1180.00")}
    out = match_gstr_2b(books=books, gstr_2b=portal)
    assert list(out.values()) == ["MATCHED"]


def test_tolerance_absorbs_paisa_delta() -> None:
    books = {_key("27AAAA0000A1Z5", "INV001"): Decimal("1180.00")}
    portal = {_key("27AAAA0000A1Z5", "INV001"): Decimal("1180.50")}
    out = match_gstr_2b(books=books, gstr_2b=portal, tolerance=Decimal("1.00"))
    assert list(out.values()) == ["MATCHED"]


def test_amount_mismatch_when_above_tolerance() -> None:
    books = {_key("27AAAA0000A1Z5", "INV001"): Decimal("1180.00")}
    portal = {_key("27AAAA0000A1Z5", "INV001"): Decimal("1200.00")}
    out = match_gstr_2b(books=books, gstr_2b=portal, tolerance=Decimal("1.00"))
    assert list(out.values()) == ["AMOUNT_MISMATCH"]


def test_missing_in_2b_flagged() -> None:
    books = {_key("27AAAA0000A1Z5", "INV001"): Decimal("1180.00")}
    out = match_gstr_2b(books=books, gstr_2b={})
    assert out[_key("27AAAA0000A1Z5", "INV001")] == "MISSING_IN_2B"


def test_missing_in_books_flagged() -> None:
    portal = {_key("27AAAA0000A1Z5", "INV001"): Decimal("1180.00")}
    out = match_gstr_2b(books={}, gstr_2b=portal)
    assert out[_key("27AAAA0000A1Z5", "INV001")] == "MISSING_IN_BOOKS"


def test_match_handles_multiple_invoices_across_categories() -> None:
    books = {
        _key("27AAAA0000A1Z5", "INV001"): Decimal("1180.00"),
        _key("27AAAA0000A1Z5", "INV002"): Decimal("2360.00"),
        _key("29BBBB1111B2Z6", "INV010"): Decimal("590.00"),
    }
    portal = {
        _key("27AAAA0000A1Z5", "INV001"): Decimal("1180.00"),    # matched
        _key("27AAAA0000A1Z5", "INV002"): Decimal("2500.00"),    # mismatch
        _key("29BBBB1111B2Z6", "INV999"): Decimal("1000.00"),    # missing-in-books
    }
    out = match_gstr_2b(books=books, gstr_2b=portal, tolerance=Decimal("1.00"))
    assert out[_key("27AAAA0000A1Z5", "INV001")] == "MATCHED"
    assert out[_key("27AAAA0000A1Z5", "INV002")] == "AMOUNT_MISMATCH"
    assert out[_key("29BBBB1111B2Z6", "INV010")] == "MISSING_IN_2B"
    assert out[_key("29BBBB1111B2Z6", "INV999")] == "MISSING_IN_BOOKS"
