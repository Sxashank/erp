"""Bank Statement and Reconciliation Schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.models.ap_ar.bank_reconciliation import (
    BankReconciliationStatus,
    ReconciliationStatus,
    StatementTransactionType,
)
from app.schemas.base import CamelSchema

# ============ Bank Statement Schemas ============


class BankStatementBase(CamelSchema):
    """Base schema for bank statement."""

    transaction_date: date
    value_date: date
    reference_number: str | None = Field(None, max_length=100)
    description: str | None = None
    transaction_type: StatementTransactionType
    debit_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    credit_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    running_balance: Decimal | None = None
    cheque_number: str | None = Field(None, max_length=20)
    utr_number: str | None = Field(None, max_length=50)
    bank_transaction_id: str | None = Field(None, max_length=100)


class BankStatementCreate(BankStatementBase):
    """Schema for creating bank statement entry."""

    bank_account_id: UUID
    organization_id: UUID


class BankStatementImportRow(CamelSchema):
    """Schema for a single row in bank statement import."""

    transaction_date: date
    value_date: date | None = None
    reference_number: str | None = None
    description: str | None = None
    debit_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    credit_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    running_balance: Decimal | None = None
    cheque_number: str | None = None
    utr_number: str | None = None


class BankStatementImport(CamelSchema):
    """Schema for importing bank statement."""

    bank_account_id: UUID
    organization_id: UUID
    rows: list[BankStatementImportRow] = Field(..., min_length=1)


class BankStatementResponse(BankStatementBase):
    """Response schema for bank statement."""

    id: UUID
    bank_account_id: UUID
    organization_id: UUID
    reconciliation_status: ReconciliationStatus
    reconciled_amount: Decimal
    reconciled_voucher_id: UUID | None
    reconciled_at: datetime | None
    import_batch_id: UUID | None
    bank_account_name: str | None = None
    unreconciled_amount: Decimal
    created_at: datetime


class BankStatementListResponse(CamelSchema):
    """List response schema for bank statement."""

    id: UUID
    transaction_date: date
    value_date: date
    reference_number: str | None
    description: str | None
    transaction_type: StatementTransactionType
    debit_amount: Decimal
    credit_amount: Decimal
    running_balance: Decimal | None
    reconciliation_status: ReconciliationStatus
    reconciled_amount: Decimal
    unreconciled_amount: Decimal


# ============ Bank Statement Match Schemas ============


class BankStatementMatchCreate(CamelSchema):
    """Schema for creating a match."""

    statement_id: UUID
    voucher_id: UUID
    matched_amount: Decimal = Field(..., gt=0)
    match_type: str = Field(default="MANUAL", max_length=20)


class BankStatementMatchResponse(CamelSchema):
    """Response schema for match."""

    id: UUID
    statement_id: UUID
    voucher_id: UUID
    matched_amount: Decimal
    match_date: date
    match_type: str
    voucher_number: str | None = None
    voucher_date: date | None = None


class AutoMatchSettings(CamelSchema):
    """Settings used for an auto-match run."""

    date_tolerance: int
    match_by_reference: bool
    match_by_cheque: bool
    match_by_utr: bool
    match_by_amount_only: bool


class AutoMatchResponse(CamelSchema):
    """Auto-match result."""

    matched_count: int
    messages: list[str]
    settings: AutoMatchSettings


# ============ Bank Reconciliation Schemas ============


class BankReconciliationBase(CamelSchema):
    """Base schema for bank reconciliation."""

    reconciliation_date: date
    from_date: date
    to_date: date
    statement_opening_balance: Decimal = Field(default=Decimal("0.00"))
    statement_closing_balance: Decimal = Field(default=Decimal("0.00"))
    book_balance: Decimal = Field(default=Decimal("0.00"))
    deposits_in_transit: Decimal = Field(default=Decimal("0.00"))
    outstanding_cheques: Decimal = Field(default=Decimal("0.00"))
    bank_charges: Decimal = Field(default=Decimal("0.00"))
    bank_interest: Decimal = Field(default=Decimal("0.00"))
    other_adjustments: Decimal = Field(default=Decimal("0.00"))
    notes: str | None = None


class BankReconciliationCreate(BankReconciliationBase):
    """Schema for creating bank reconciliation."""

    bank_account_id: UUID
    organization_id: UUID


class BankReconciliationUpdate(CamelSchema):
    """Schema for updating bank reconciliation."""

    statement_opening_balance: Decimal | None = None
    statement_closing_balance: Decimal | None = None
    deposits_in_transit: Decimal | None = None
    outstanding_cheques: Decimal | None = None
    bank_charges: Decimal | None = None
    bank_interest: Decimal | None = None
    other_adjustments: Decimal | None = None
    notes: str | None = None


class BankReconciliationResponse(BankReconciliationBase):
    """Response schema for bank reconciliation."""

    id: UUID
    bank_account_id: UUID
    organization_id: UUID
    reconciled_balance: Decimal
    difference: Decimal
    status: BankReconciliationStatus
    completed_at: datetime | None
    bank_account_name: str | None = None
    created_at: datetime
    updated_at: datetime | None


# ============ BRS Report Schemas ============


class BRSReportItem(CamelSchema):
    """Individual item in BRS report."""

    id: UUID
    date: date
    reference: str
    description: str | None
    amount: Decimal
    item_type: str  # DEPOSIT_IN_TRANSIT, OUTSTANDING_CHEQUE, BANK_CHARGE, etc.


class BRSReportResponse(CamelSchema):
    """Bank Reconciliation Statement report response."""

    bank_account_id: UUID
    bank_account_name: str
    reconciliation_date: date
    from_date: date
    to_date: date

    # Per Bank Statement
    statement_opening_balance: Decimal
    statement_closing_balance: Decimal

    # Per Books
    book_opening_balance: Decimal
    book_closing_balance: Decimal

    # Reconciliation Items
    deposits_in_transit: list[BRSReportItem]
    outstanding_cheques: list[BRSReportItem]
    credits_in_bank_not_books: list[BRSReportItem]
    debits_in_bank_not_books: list[BRSReportItem]

    # Summary
    total_deposits_in_transit: Decimal
    total_outstanding_cheques: Decimal
    total_credits_not_in_books: Decimal
    total_debits_not_in_books: Decimal
    reconciled_balance: Decimal
    difference: Decimal


# ============ Unreconciled Items Schemas ============


class UnreconciledBookEntry(CamelSchema):
    """Unreconciled entry from books."""

    voucher_id: UUID
    voucher_number: str
    voucher_date: date
    narration: str | None
    debit_amount: Decimal
    credit_amount: Decimal
    entry_type: str  # PAYMENT, RECEIPT, JOURNAL


class UnreconciledStatementEntry(CamelSchema):
    """Unreconciled entry from bank statement."""

    statement_id: UUID
    transaction_date: date
    reference_number: str | None
    description: str | None
    debit_amount: Decimal
    credit_amount: Decimal
    unreconciled_amount: Decimal


class ReconciliationWorkspaceResponse(CamelSchema):
    """Response for reconciliation workspace."""

    bank_account_id: UUID
    bank_account_name: str
    from_date: date
    to_date: date

    # Unreconciled items
    unreconciled_statements: list[UnreconciledStatementEntry]
    unreconciled_book_entries: list[UnreconciledBookEntry]

    # Summary
    total_unreconciled_bank_credits: Decimal
    total_unreconciled_bank_debits: Decimal
    total_unreconciled_book_credits: Decimal
    total_unreconciled_book_debits: Decimal
