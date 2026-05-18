"""Payment File schemas."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelSchema


class PaymentFileFormat(StrEnum):
    """Payment file formats."""
    NEFT = "NEFT"
    RTGS = "RTGS"
    IMPS = "IMPS"
    UPI = "UPI"


class PaymentFileStatus(StrEnum):
    """Payment file status."""
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    DOWNLOADED = "DOWNLOADED"
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"


class PaymentTransactionStatus(StrEnum):
    """Payment transaction status within a file."""
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class PaymentFileCreate(CamelSchema):
    """Schema for creating a payment file."""
    organization_id: UUID
    organization_bank_account_id: UUID
    file_format: PaymentFileFormat
    payment_date: date
    payment_ids: list[UUID] = Field(..., min_length=1)
    description: str | None = None


class PaymentFileTransactionCreate(CamelSchema):
    """Schema for payment file transaction."""
    payment_id: UUID
    beneficiary_name: str = Field(..., max_length=100)
    beneficiary_account_number: str = Field(..., max_length=34)
    beneficiary_ifsc: str = Field(..., max_length=11)
    beneficiary_bank_name: str | None = Field(None, max_length=100)
    amount: Decimal = Field(..., gt=0)
    narration: str | None = Field(None, max_length=100)
    email: str | None = None
    mobile: str | None = None


class PaymentFileTransactionResponse(CamelSchema):
    """Response schema for payment file transaction."""
    id: UUID
    payment_file_id: UUID
    payment_id: UUID
    sequence_number: int
    beneficiary_name: str
    beneficiary_account_number: str
    beneficiary_ifsc: str
    beneficiary_bank_name: str | None
    amount: Decimal
    narration: str | None
    status: PaymentTransactionStatus
    bank_reference: str | None
    failure_reason: str | None
    processed_at: datetime | None


class PaymentFileResponse(CamelSchema):
    """Response schema for payment file."""
    id: UUID
    organization_id: UUID
    organization_bank_account_id: UUID
    file_reference: str
    file_format: PaymentFileFormat
    payment_date: date
    status: PaymentFileStatus
    total_transactions: int
    total_amount: Decimal
    successful_count: int
    failed_count: int
    file_generated_at: datetime | None
    file_downloaded_at: datetime | None
    file_uploaded_at: datetime | None
    processing_started_at: datetime | None
    processing_completed_at: datetime | None
    description: str | None
    created_at: datetime
    created_by: UUID | None


class PaymentFileDetailResponse(PaymentFileResponse):
    """Detailed response with transactions."""
    transactions: list[PaymentFileTransactionResponse] = []


class PaymentFileListResponse(CamelSchema):
    """List response for payment files."""
    items: list[PaymentFileResponse]
    total: int
    skip: int
    limit: int


class PaymentFileGenerateRequest(CamelSchema):
    """Request for generating a payment file."""
    organization_id: UUID
    organization_bank_account_id: UUID
    file_format: PaymentFileFormat
    payment_date: date
    payment_ids: list[UUID] = Field(..., min_length=1)
    description: str | None = None


class PaymentFileUploadResponse(CamelSchema):
    """Response after marking file as uploaded."""
    id: UUID
    file_reference: str
    status: PaymentFileStatus
    uploaded_at: datetime


class PaymentFileProcessingUpdate(CamelSchema):
    """Update schema for processing results."""
    transactions: list[dict]  # List of {payment_id, status, bank_reference, failure_reason}


class BankFormatConfig(CamelSchema):
    """Bank-specific file format configuration."""
    bank_code: str = Field(..., max_length=10)
    bank_name: str = Field(..., max_length=100)
    neft_format: str | None = "NPCI_STANDARD"
    rtgs_format: str | None = "NPCI_STANDARD"
    imps_format: str | None = None
    header_format: dict | None = None
    trailer_format: dict | None = None
    delimiter: str = "|"
    date_format: str = "%d/%m/%Y"
    amount_format: str = "decimal"  # decimal or paise
    encoding: str = "utf-8"


class NEFTFileRecord(CamelSchema):
    """NEFT file record structure."""
    serial_number: int
    destination_ifsc: str
    beneficiary_account_number: str
    beneficiary_name: str
    amount: Decimal
    remitter_account_number: str
    remitter_name: str
    payment_type: str = "IFT"  # Inter Fund Transfer
    narration: str | None = None
    email: str | None = None
    mobile: str | None = None


class RTGSFileRecord(CamelSchema):
    """RTGS file record structure."""
    serial_number: int
    destination_ifsc: str
    beneficiary_account_number: str
    beneficiary_name: str
    amount: Decimal
    remitter_account_number: str
    remitter_name: str
    payment_type: str = "RTG"
    narration: str | None = None
    sender_to_receiver_info: str | None = None


class PaymentFileSummary(CamelSchema):
    """Summary of payments for file generation."""
    total_payments: int
    total_amount: Decimal
    by_format: dict  # {NEFT: {count, amount}, RTGS: {count, amount}}
    eligible_for_generation: int
    already_in_file: int
