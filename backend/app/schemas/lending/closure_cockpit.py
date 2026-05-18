"""Loan closure and security release cockpit response schemas."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from app.schemas.base import CamelSchema


class ClosureCockpitSummary(CamelSchema):
    """Portfolio-level loan closure, NOC and collateral release KPIs."""

    closure_ready_count: int
    closure_ready_outstanding: Decimal
    closed_pending_release_count: int
    unreleased_security_count: int
    unreleased_security_value: Decimal
    recent_closure_receipt_count: int
    recent_closure_receipt_amount: Decimal
    blocked_by_outstanding_count: int
    blocked_by_outstanding_amount: Decimal


class ClosureCandidateItem(CamelSchema):
    """Loan account that is ready or near-ready for manual closure review."""

    loan_account_id: UUID
    loan_account_number: str
    borrower_name: str
    status: str
    total_outstanding: Decimal
    principal_outstanding: Decimal
    interest_outstanding: Decimal
    charges_outstanding: Decimal
    maturity_date: str | None = None
    closure_date: str | None = None
    closure_status: str
    unreleased_security_count: int
    unreleased_security_value: Decimal
    original_documents_held: int


class SecurityReleaseItem(CamelSchema):
    """Security/document release item pending after closure readiness."""

    security_id: UUID
    loan_account_id: UUID
    loan_account_number: str
    borrower_name: str
    security_type: str
    security_category: str
    description: str
    acceptable_value: Decimal
    net_value: Decimal
    status: str
    original_documents_received: bool
    document_location: str | None = None
    release_date: str | None = None


class RecentClosureReceiptItem(CamelSchema):
    """Manual prepayment, foreclosure, OTS or recovery receipt relevant to closure."""

    receipt_id: UUID
    loan_account_id: UUID
    loan_account_number: str
    borrower_name: str
    receipt_number: str
    receipt_date: str
    receipt_type: str
    receipt_amount: Decimal
    allocated_amount: Decimal
    unallocated_amount: Decimal
    status: str
    instrument_number: str | None = None


class ClosureCockpitResponse(CamelSchema):
    """Aggregate envelope returned by /api/v1/lending/closure-cockpit."""

    summary: ClosureCockpitSummary
    closure_candidates: list[ClosureCandidateItem]
    pending_security_releases: list[SecurityReleaseItem]
    recent_closure_receipts: list[RecentClosureReceiptItem]
