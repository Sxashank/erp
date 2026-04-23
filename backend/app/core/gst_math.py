"""GST computation helpers — portal-free, pure-math.

CLAUDE.md §4.5 / §7.1:
  - Intra-state supply → CGST + SGST (each half the total rate).
  - Inter-state supply → IGST (full total rate).
  - RCM (reverse charge) triggers:
      * unregistered vendor + aggregate > ₹5000/day for notified categories, OR
      * explicit RCM-notified HSN regardless of vendor registration.
  - ITC is BLOCKED on certain categories (motor vehicles, personal
    consumption, food/beverages, memberships, works contract for
    immovable property, etc.).

This module is IMPORTED by sales/purchase services and by the Arq
`generate_gstr_dump` job. No DB, no portal calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

RCM_DAILY_THRESHOLD = Decimal("5000")  # ₹5,000/day from unregistered vendor


@dataclass(frozen=True)
class GSTBreakdown:
    taxable_value: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    cess_amount: Decimal
    total_tax: Decimal
    total_invoice_value: Decimal


def _q(x: Decimal) -> Decimal:
    """Round to 2 decimal places, ROUND_HALF_UP (matches GSTN portal)."""
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_gst(
    *,
    taxable_value: Decimal,
    gst_rate_pct: Decimal,
    is_interstate: bool,
    cess_rate_pct: Decimal = Decimal("0"),
) -> GSTBreakdown:
    """Compute CGST/SGST or IGST for a single line item.

    Args:
      taxable_value:   the pre-tax amount (NUMERIC(18,2)).
      gst_rate_pct:    total GST rate (e.g. 18 for 18%).
      is_interstate:   True → IGST; False → CGST + SGST.
      cess_rate_pct:   GST compensation cess if applicable.
    """
    if taxable_value < 0:
        raise ValueError("taxable_value must be non-negative")
    if gst_rate_pct < 0:
        raise ValueError("gst_rate_pct must be non-negative")
    if cess_rate_pct < 0:
        raise ValueError("cess_rate_pct must be non-negative")

    half = gst_rate_pct / Decimal("2")
    if is_interstate:
        cgst = Decimal("0")
        sgst = Decimal("0")
        igst = _q(taxable_value * gst_rate_pct / Decimal("100"))
    else:
        cgst = _q(taxable_value * half / Decimal("100"))
        sgst = _q(taxable_value * half / Decimal("100"))
        igst = Decimal("0")

    cess = _q(taxable_value * cess_rate_pct / Decimal("100"))
    total_tax = cgst + sgst + igst + cess

    return GSTBreakdown(
        taxable_value=taxable_value,
        cgst_amount=cgst,
        sgst_amount=sgst,
        igst_amount=igst,
        cess_amount=cess,
        total_tax=total_tax,
        total_invoice_value=taxable_value + total_tax,
    )


# ---------------------------------------------------------------------------
# RCM applicability.
# ---------------------------------------------------------------------------

# HSN codes where RCM applies regardless of vendor registration. Not
# exhaustive — extend as the registrar publishes new notifications.
NOTIFIED_RCM_HSN_CODES: frozenset[str] = frozenset({
    # GTA (goods transport agency) services
    "996511",
    "996512",
    # Legal services by advocate / firm to business entity
    "998212",
    "998213",
    # Services by an individual author / composer / photographer to publisher
    "999291",
    # Services by director of a company to the company
    "998595",
    # Sponsorship services provided to body corporate / partnership
    "998559",
    # Import of services (any HSN) — caller must set is_import=True
})


def is_rcm_applicable(
    *,
    vendor_is_registered: bool,
    is_import: bool = False,
    hsn_code: str | None = None,
    today_aggregate_from_vendor: Decimal = Decimal("0"),
) -> bool:
    """Decide if reverse-charge mechanism (RCM) applies to a purchase.

    RCM triggers when:
      1. HSN code is on the notified RCM list, OR
      2. The supply is an import of services, OR
      3. The vendor is unregistered AND the buyer's cumulative purchases
         from that vendor today already exceed ₹5,000.
    """
    if hsn_code and hsn_code in NOTIFIED_RCM_HSN_CODES:
        return True
    if is_import:
        return True
    if not vendor_is_registered and today_aggregate_from_vendor > RCM_DAILY_THRESHOLD:
        return True
    return False


# ---------------------------------------------------------------------------
# Blocked credits (ITC ineligible) — §17(5) CGST Act.
# ---------------------------------------------------------------------------

# Expense categories that NEVER carry ITC. Using strings the rest of the
# app already uses in the `expense_category` field on purchase bills.
BLOCKED_ITC_CATEGORIES: frozenset[str] = frozenset({
    "MOTOR_VEHICLE",          # §17(5)(a)
    "FOOD_AND_BEVERAGES",     # §17(5)(b)(i)
    "OUTDOOR_CATERING",       # §17(5)(b)(i)
    "BEAUTY_TREATMENT",       # §17(5)(b)(i)
    "HEALTH_SERVICES",        # §17(5)(b)(i)
    "CLUB_MEMBERSHIP",        # §17(5)(b)(ii)
    "LIFE_INSURANCE",         # §17(5)(b)(i)
    "HEALTH_INSURANCE",       # §17(5)(b)(i) (employee only)
    "TRAVEL_BENEFITS",        # §17(5)(b)(iv) — LTA/holiday
    "WORKS_CONTRACT_IMMOVABLE",   # §17(5)(c) — construction of immovable property
    "CONSTRUCTION_IMMOVABLE",     # §17(5)(d)
    "PERSONAL_CONSUMPTION",   # §17(5)(g)
    "LOST_DESTROYED_GIFTS",   # §17(5)(h)
})


def is_itc_blocked(expense_category: str | None) -> bool:
    """Return True if the expense category is in the blocked-credits list."""
    if not expense_category:
        return False
    return expense_category.upper() in BLOCKED_ITC_CATEGORIES


# ---------------------------------------------------------------------------
# GSTR-2B ↔ purchase-register matching.
# ---------------------------------------------------------------------------

MatchStatus = Literal["MATCHED", "AMOUNT_MISMATCH", "MISSING_IN_2B", "MISSING_IN_BOOKS"]


@dataclass(frozen=True)
class GSTInvoiceKey:
    """Normalised invoice identity used for matching."""
    gstin_supplier: str
    invoice_number: str
    invoice_date: str  # ISO yyyy-mm-dd


def match_gstr_2b(
    *,
    books: dict[GSTInvoiceKey, Decimal],
    gstr_2b: dict[GSTInvoiceKey, Decimal],
    tolerance: Decimal = Decimal("1.00"),
) -> dict[GSTInvoiceKey, MatchStatus]:
    """Match the org's purchase register against the GSTR-2B auto-populated data.

    Returns a mapping of every key seen on either side to its status:
      - MATCHED: present on both, amounts within ±tolerance.
      - AMOUNT_MISMATCH: present on both, amount delta exceeds tolerance.
      - MISSING_IN_2B: in books, not in GSTR-2B (vendor hasn't filed GSTR-1).
      - MISSING_IN_BOOKS: in 2B, not in books (missed entry or fraud).
    """
    result: dict[GSTInvoiceKey, MatchStatus] = {}
    for key, book_amount in books.items():
        if key not in gstr_2b:
            result[key] = "MISSING_IN_2B"
            continue
        delta = abs(book_amount - gstr_2b[key])
        result[key] = "MATCHED" if delta <= tolerance else "AMOUNT_MISMATCH"
    for key in gstr_2b.keys() - books.keys():
        result[key] = "MISSING_IN_BOOKS"
    return result
