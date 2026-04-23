"""Payment File schemas."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentFileFormat(str, Enum):
    """Payment file formats."""
    NEFT = "NEFT"
    RTGS = "RTGS"
    IMPS = "IMPS"
    UPI = "UPI"


class PaymentFileStatus(str, Enum):
    """Payment file status."""
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    DOWNLOADED = "DOWNLOADED"
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"


class PaymentTransactionStatus(str, Enum):
    """Payment transaction status within a file."""
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class PaymentFileCreate(BaseModel):
    """Schema for creating a payment file."""
    organization_id: UUID
    organization_bank_account_id: UUID
    file_format: PaymentFileFormat
    payment_date: date
    payment_ids: List[UUID] = Field(..., min_length=1)
    description: Optional[str] = None


class PaymentFileTransactionCreate(BaseModel):
    """Schema for payment file transaction."""
    payment_id: UUID
    beneficiary_name: str = Field(..., max_length=100)
    beneficiary_account_number: str = Field(..., max_length=34)
    beneficiary_ifsc: str = Field(..., max_length=11)
    beneficiary_bank_name: Optional[str] = Field(None, max_length=100)
    amount: Decimal = Field(..., gt=0)
    narration: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = None
    mobile: Optional[str] = None


class PaymentFileTransactionResponse(BaseModel):
    """Response schema for payment file transaction."""
    id: UUID
    payment_file_id: UUID
    payment_id: UUID
    sequence_number: int
    beneficiary_name: str
    beneficiary_account_number: str
    beneficiary_ifsc: str
    beneficiary_bank_name: Optional[str]
    amount: Decimal
    narration: Optional[str]
    status: PaymentTransactionStatus
    bank_reference: Optional[str]
    failure_reason: Optional[str]
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class PaymentFileResponse(BaseModel):
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
    file_generated_at: Optional[datetime]
    file_downloaded_at: Optional[datetime]
    file_uploaded_at: Optional[datetime]
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    description: Optional[str]
    created_at: datetime
    created_by: Optional[UUID]

    class Config:
        from_attributes = True


class PaymentFileDetailResponse(PaymentFileResponse):
    """Detailed response with transactions."""
    transactions: List[PaymentFileTransactionResponse] = []


class PaymentFileListResponse(BaseModel):
    """List response for payment files."""
    items: List[PaymentFileResponse]
    total: int
    skip: int
    limit: int


class PaymentFileGenerateRequest(BaseModel):
    """Request for generating a payment file."""
    organization_id: UUID
    organization_bank_account_id: UUID
    file_format: PaymentFileFormat
    payment_date: date
    payment_ids: List[UUID] = Field(..., min_length=1)
    description: Optional[str] = None


class PaymentFileUploadResponse(BaseModel):
    """Response after marking file as uploaded."""
    id: UUID
    file_reference: str
    status: PaymentFileStatus
    uploaded_at: datetime


class PaymentFileProcessingUpdate(BaseModel):
    """Update schema for processing results."""
    transactions: List[dict]  # List of {payment_id, status, bank_reference, failure_reason}


class BankFormatConfig(BaseModel):
    """Bank-specific file format configuration."""
    bank_code: str = Field(..., max_length=10)
    bank_name: str = Field(..., max_length=100)
    neft_format: Optional[str] = "NPCI_STANDARD"
    rtgs_format: Optional[str] = "NPCI_STANDARD"
    imps_format: Optional[str] = None
    header_format: Optional[dict] = None
    trailer_format: Optional[dict] = None
    delimiter: str = "|"
    date_format: str = "%d/%m/%Y"
    amount_format: str = "decimal"  # decimal or paise
    encoding: str = "utf-8"


class NEFTFileRecord(BaseModel):
    """NEFT file record structure."""
    serial_number: int
    destination_ifsc: str
    beneficiary_account_number: str
    beneficiary_name: str
    amount: Decimal
    remitter_account_number: str
    remitter_name: str
    payment_type: str = "IFT"  # Inter Fund Transfer
    narration: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None


class RTGSFileRecord(BaseModel):
    """RTGS file record structure."""
    serial_number: int
    destination_ifsc: str
    beneficiary_account_number: str
    beneficiary_name: str
    amount: Decimal
    remitter_account_number: str
    remitter_name: str
    payment_type: str = "RTG"
    narration: Optional[str] = None
    sender_to_receiver_info: Optional[str] = None


class PaymentFileSummary(BaseModel):
    """Summary of payments for file generation."""
    total_payments: int
    total_amount: Decimal
    by_format: dict  # {NEFT: {count, amount}, RTGS: {count, amount}}
    eligible_for_generation: int
    already_in_file: int
