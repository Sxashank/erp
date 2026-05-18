"""Repayment matching schemas for bank-statement credit detection."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.schemas.base import CamelSchema


class RepaymentMatchCandidate(CamelSchema):
    """One candidate match between a bank credit and a loan receipt/demand."""

    statement_id: UUID
    transaction_date: date
    value_date: date
    reference_number: str | None = None
    utr_number: str | None = None
    description: str | None = None
    credit_amount: Decimal
    suggested_loan_account_id: UUID | None = None
    loan_account_number: str | None = None
    entity_name: str | None = None
    suggested_receipt_id: UUID | None = None
    suggested_installment_id: UUID | None = None
    due_date: date | None = None
    due_amount: Decimal | None = None
    confidence: Decimal
    match_basis: list[str]
    suggested_action: str


class RepaymentMatchingSummary(CamelSchema):
    """Summary of imported credits available for repayment matching."""

    unmatched_credit_count: int
    unmatched_credit_amount: Decimal
    high_confidence_count: int
    review_required_count: int


class RepaymentMatchingResponse(CamelSchema):
    """Candidate list plus summary for a repayment matching workbench."""

    summary: RepaymentMatchingSummary
    candidates: list[RepaymentMatchCandidate]


class CreateMatchedReceiptRequest(CamelSchema):
    """Create a loan receipt from an imported bank credit."""

    loan_account_id: UUID | None = None
    auto_allocate: bool = True


class CreateMatchedReceiptResponse(CamelSchema):
    """Receipt created from a bank-statement match candidate."""

    statement_id: UUID
    match_id: UUID
    receipt_id: UUID
    receipt_number: str
    loan_account_id: UUID
    receipt_amount: Decimal
    allocated_amount: Decimal
    unallocated_amount: Decimal
    statement_status: str
    match_confidence: Decimal
    match_type: str
    match_basis: dict[str, Any]
