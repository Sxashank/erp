"""Bank Statement and Reconciliation Schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.ap_ar.bank_reconciliation import (
    StatementTransactionType,
    ReconciliationStatus,
    BankReconciliationStatus,
)


# ============ Bank Statement Schemas ============


class BankStatementBase(BaseModel):
    """Base schema for bank statement."""

    transaction_date: date
    value_date: date
    reference_number: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    transaction_type: StatementTransactionType
    debit_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    credit_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    running_balance: Optional[Decimal] = None
    cheque_number: Optional[str] = Field(None, max_length=20)
    utr_number: Optional[str] = Field(None, max_length=50)
    bank_transaction_id: Optional[str] = Field(None, max_length=100)


class BankStatementCreate(BankStatementBase):
    """Schema for creating bank statement entry."""

    bank_account_id: UUID
    organization_id: UUID


class BankStatementImportRow(BaseModel):
    """Schema for a single row in bank statement import."""

    transaction_date: date
    value_date: Optional[date] = None
    reference_number: Optional[str] = None
    description: Optional[str] = None
    debit_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    credit_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    running_balance: Optional[Decimal] = None
    cheque_number: Optional[str] = None
    utr_number: Optional[str] = None


class BankStatementImport(BaseModel):
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
    reconciled_voucher_id: Optional[UUID]
    reconciled_at: Optional[datetime]
    import_batch_id: Optional[UUID]
    bank_account_name: Optional[str] = None
    unreconciled_amount: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class BankStatementListResponse(BaseModel):
    """List response schema for bank statement."""

    id: UUID
    transaction_date: date
    value_date: date
    reference_number: Optional[str]
    description: Optional[str]
    transaction_type: StatementTransactionType
    debit_amount: Decimal
    credit_amount: Decimal
    running_balance: Optional[Decimal]
    reconciliation_status: ReconciliationStatus
    reconciled_amount: Decimal
    unreconciled_amount: Decimal

    class Config:
        from_attributes = True


# ============ Bank Statement Match Schemas ============


class BankStatementMatchCreate(BaseModel):
    """Schema for creating a match."""

    statement_id: UUID
    voucher_id: UUID
    matched_amount: Decimal = Field(..., gt=0)
    match_type: str = Field(default="MANUAL", max_length=20)


class BankStatementMatchResponse(BaseModel):
    """Response schema for match."""

    id: UUID
    statement_id: UUID
    voucher_id: UUID
    matched_amount: Decimal
    match_date: date
    match_type: str
    voucher_number: Optional[str] = None
    voucher_date: Optional[date] = None

    class Config:
        from_attributes = True


# ============ Bank Reconciliation Schemas ============


class BankReconciliationBase(BaseModel):
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
    notes: Optional[str] = None


class BankReconciliationCreate(BankReconciliationBase):
    """Schema for creating bank reconciliation."""

    bank_account_id: UUID
    organization_id: UUID


class BankReconciliationUpdate(BaseModel):
    """Schema for updating bank reconciliation."""

    statement_opening_balance: Optional[Decimal] = None
    statement_closing_balance: Optional[Decimal] = None
    deposits_in_transit: Optional[Decimal] = None
    outstanding_cheques: Optional[Decimal] = None
    bank_charges: Optional[Decimal] = None
    bank_interest: Optional[Decimal] = None
    other_adjustments: Optional[Decimal] = None
    notes: Optional[str] = None


class BankReconciliationResponse(BankReconciliationBase):
    """Response schema for bank reconciliation."""

    id: UUID
    bank_account_id: UUID
    organization_id: UUID
    reconciled_balance: Decimal
    difference: Decimal
    status: BankReconciliationStatus
    completed_at: Optional[datetime]
    bank_account_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============ BRS Report Schemas ============


class BRSReportItem(BaseModel):
    """Individual item in BRS report."""

    id: UUID
    date: date
    reference: str
    description: Optional[str]
    amount: Decimal
    item_type: str  # DEPOSIT_IN_TRANSIT, OUTSTANDING_CHEQUE, BANK_CHARGE, etc.


class BRSReportResponse(BaseModel):
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

    class Config:
        from_attributes = True


# ============ Unreconciled Items Schemas ============


class UnreconciledBookEntry(BaseModel):
    """Unreconciled entry from books."""

    voucher_id: UUID
    voucher_number: str
    voucher_date: date
    narration: Optional[str]
    debit_amount: Decimal
    credit_amount: Decimal
    entry_type: str  # PAYMENT, RECEIPT, JOURNAL

    class Config:
        from_attributes = True


class UnreconciledStatementEntry(BaseModel):
    """Unreconciled entry from bank statement."""

    statement_id: UUID
    transaction_date: date
    reference_number: Optional[str]
    description: Optional[str]
    debit_amount: Decimal
    credit_amount: Decimal
    unreconciled_amount: Decimal

    class Config:
        from_attributes = True


class ReconciliationWorkspaceResponse(BaseModel):
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

    class Config:
        from_attributes = True
