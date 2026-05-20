"""Configurable IIF scheme rules.

The guideline is stable enough to have defaults, but notifications may change
rates, documents, SLAs, eligibility evidence or calculation basis. Keep those as
scheme-level JSON config and centralise interpretation here.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from decimal import Decimal
from typing import Any


CALCULATION_RATE_ON_PRINCIPAL_DAYS = "RATE_DIFFERENTIAL_ON_PRINCIPAL_DAYS"
CALCULATION_PERCENT_OF_INTEREST_PAID = "PERCENT_OF_INTEREST_PAID"


DEFAULT_CALCULATION_RULES: dict[str, Any] = {
    "method": CALCULATION_RATE_ON_PRINCIPAL_DAYS,
    "day_count": "ACT_365",
    "cap_by_actual_interest_paid": True,
    "compute_per_tranche": True,
}

DEFAULT_ELIGIBILITY_RULES: dict[str, Any] = {
    "require_shipyard_located_in_india": True,
    "require_lender_regulated_in_india": True,
    "require_not_wilful_defaulter": True,
    "exclude_refinance_takeover_restructure": True,
    "exclude_overdue_or_npa": True,
    "require_sanction_after_scheme_approval": True,
    "require_lender_forwarding_same_quarter": True,
}

DEFAULT_REQUIRED_DOCUMENTS: list[dict[str, Any]] = [
    {"code": "LOAN_SANCTION_LETTER", "stage": "TAGGING", "label": "Loan sanction letter"},
    {"code": "APPRAISAL_NOTE", "stage": "TAGGING", "label": "Project appraisal note"},
    {"code": "DISBURSEMENT_DETAILS", "stage": "TAGGING", "label": "Disbursement details"},
    {"code": "END_USE_CERTIFICATE", "stage": "TAGGING", "label": "End-use certificate"},
    {
        "code": "BORROWER_COMPLIANCE_DOCUMENTS",
        "stage": "TAGGING",
        "label": "Borrower compliance documents",
    },
    {
        "code": "INTEREST_CALCULATION_SHEET",
        "stage": "CLAIM_SUBMISSION",
        "label": "Interest calculation sheet",
    },
    {
        "code": "REPAYMENT_RECORD",
        "stage": "CLAIM_SUBMISSION",
        "label": "Borrower repayment record",
    },
    {
        "code": "REGULAR_ACCOUNT_CERTIFICATE",
        "stage": "CLAIM_SUBMISSION",
        "label": "Certificate of regular account status",
    },
    {
        "code": "NON_DUPLICATION_UNDERTAKING",
        "stage": "CLAIM_SUBMISSION",
        "label": "Undertaking on non-duplication of claims",
    },
    {
        "code": "AUDITED_INTEREST_CERTIFICATE",
        "stage": "CLAIM_SUBMISSION",
        "label": "Audited interest certificate",
    },
    {"code": "CLAIM_SUMMARY", "stage": "CLAIM_SUBMISSION", "label": "Claim summary"},
]

DEFAULT_WORKFLOW_RULES: dict[str, Any] = {
    "claim_creator_roles": ["scheme_lender", "scheme_borrower", "scheme_admin"],
    "formal_submitter_roles": ["scheme_lender", "scheme_admin"],
    "ia_decision_sla_days": 30,
    "release_sla_days": 7,
    "release_destination": "BORROWER_LOAN_ACCOUNT",
    "require_nodal_officer": True,
    "require_grievance_cell": True,
}

DEFAULT_FUND_RULES: dict[str, Any] = {
    "dedicated_bank_account_required": True,
    "service_charge_first_year_percent_of_corpus": "0.10",
    "service_charge_subsequent_year_percent_of_corpus": "0.072",
    "allocation_frequency": "ANNUAL",
    "manual_neft_rtgs_reference_required": True,
}


def merge_rules(defaults: dict[str, Any], override: dict[str, Any] | None) -> dict[str, Any]:
    """Return defaults overlaid with non-null scheme overrides."""
    merged = dict(defaults)
    for key, value in (override or {}).items():
        if value is not None:
            merged[key] = value
    return merged


def calculation_rules(scheme: Any) -> dict[str, Any]:
    return merge_rules(DEFAULT_CALCULATION_RULES, getattr(scheme, "calculation_rules", None))


def eligibility_rules(scheme: Any) -> dict[str, Any]:
    return merge_rules(DEFAULT_ELIGIBILITY_RULES, getattr(scheme, "eligibility_rules", None))


def workflow_rules(scheme: Any) -> dict[str, Any]:
    return merge_rules(DEFAULT_WORKFLOW_RULES, getattr(scheme, "workflow_rules", None))


def fund_rules(scheme: Any) -> dict[str, Any]:
    return merge_rules(DEFAULT_FUND_RULES, getattr(scheme, "fund_rules", None))


def required_documents(scheme: Any, *, stage: str | None = None) -> list[dict[str, Any]]:
    rows = getattr(scheme, "required_documents", None) or DEFAULT_REQUIRED_DOCUMENTS
    if not stage:
        return list(rows)
    stage_key = stage.upper()
    return [row for row in rows if str(row.get("stage", "")).upper() == stage_key]


def normalize_document_code(value: str | None) -> str:
    raw = (value or "").strip().upper()
    return re.sub(r"[^A-Z0-9]+", "_", raw).strip("_")


def supplied_document_codes(documents: Iterable[dict[str, Any]]) -> set[str]:
    codes: set[str] = set()
    for doc in documents:
        if not isinstance(doc, dict):
            continue
        for key in ("document_category", "code", "name", "file_name"):
            normalized = normalize_document_code(str(doc.get(key) or ""))
            if normalized:
                codes.add(normalized)
    return codes


def missing_required_documents(
    scheme: Any,
    documents: Iterable[dict[str, Any]],
    *,
    stage: str,
) -> list[str]:
    supplied = supplied_document_codes(documents)
    missing: list[str] = []
    for requirement in required_documents(scheme, stage=stage):
        code = normalize_document_code(str(requirement.get("code") or ""))
        aliases = {
            normalize_document_code(str(alias))
            for alias in requirement.get("aliases", [])
            if alias
        }
        if code and code not in supplied and not (aliases & supplied):
            missing.append(str(requirement.get("label") or code))
    return missing


def decimal_bool(value: Any) -> bool:
    """Treat Decimal/number/string booleans from JSON-like metadata safely."""
    if isinstance(value, bool):
        return value
    if isinstance(value, Decimal):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)
