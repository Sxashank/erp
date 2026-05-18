"""Collection and reconciliation cockpit response schemas."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from app.schemas.base import CamelSchema


class CollectionCockpitSummary(CamelSchema):
    """Period-level collection, allocation and matching KPIs."""

    period_from: str
    period_to: str
    demand_amount: Decimal
    receipt_amount: Decimal
    allocated_amount: Decimal
    unallocated_receipts: Decimal
    collection_efficiency_percent: Decimal
    overdue_amount: Decimal
    overdue_accounts: int
    unmatched_bank_credit_count: int
    unmatched_bank_credit_amount: Decimal
    matched_bank_credit_count: int
    matched_bank_credit_amount: Decimal


class CollectionBucketMetric(CamelSchema):
    """Due ageing bucket for borrower receivables."""

    bucket: str
    label: str
    installment_count: int
    amount_due: Decimal
    portfolio_percent: Decimal


class UpcomingCollectionItem(CamelSchema):
    """Installment or interest demand requiring follow-up."""

    loan_account_id: UUID
    loan_account_number: str
    borrower_name: str
    due_date: str
    installment_number: int
    status: str
    days_past_due: int
    principal_due: Decimal
    interest_due: Decimal
    penal_due: Decimal
    amount_due: Decimal


class UnmatchedBankCreditItem(CamelSchema):
    """Imported bank credit pending allocation to a borrower receipt."""

    statement_id: UUID
    transaction_date: str
    value_date: str
    reference_number: str | None = None
    utr_number: str | None = None
    description: str | None = None
    credit_amount: Decimal
    reconciled_amount: Decimal
    unreconciled_amount: Decimal


class CollectionCockpitResponse(CamelSchema):
    """Aggregate envelope returned by /api/v1/lending/collection-cockpit."""

    summary: CollectionCockpitSummary
    ageing_buckets: list[CollectionBucketMetric]
    upcoming_collections: list[UpcomingCollectionItem]
    unmatched_bank_credits: list[UnmatchedBankCreditItem]
