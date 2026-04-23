"""NACH file format schemas and data structures."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class NachFileRecord(BaseModel):
    """Base record for NACH file."""
    record_type: str = "D"  # D=Debit, C=Credit


class NachDebitRecord(BaseModel):
    """Individual debit record in NACH ACH file format."""

    # Record identification
    record_type: str = Field(default="D", description="D for Debit")

    # Transaction reference
    transaction_reference: str = Field(..., max_length=30, description="Unique transaction reference")

    # Mandate details
    umrn: str = Field(..., max_length=20, description="Unique Mandate Reference Number")

    # Beneficiary (source account for debit)
    account_number: str = Field(..., max_length=35, description="Account number to debit")
    ifsc_code: str = Field(..., max_length=11, description="IFSC code")
    account_holder_name: str = Field(..., max_length=40, description="Account holder name")
    bank_name: Optional[str] = Field(None, max_length=40)

    # Amount
    amount: Decimal = Field(..., description="Debit amount in paise")

    # Date
    debit_date: date = Field(..., description="Date of debit")

    # Corporate details (sponsor bank)
    sponsor_bank_ifsc: str = Field(..., max_length=11, description="Sponsor bank IFSC")
    utility_code: str = Field(..., max_length=18, description="Utility code assigned by NPCI")

    # Narration
    narration: str = Field(default="EMI DEBIT", max_length=30)

    def to_ach_line(self) -> str:
        """Convert to ACH file format line (fixed width)."""
        # ACH format is typically fixed-width fields
        # This is a simplified version - actual format may vary by provider
        amount_paise = int(self.amount * 100)

        line_parts = [
            self.record_type.ljust(1),
            self.transaction_reference.ljust(30),
            self.umrn.ljust(20),
            self.account_number.ljust(35),
            self.ifsc_code.ljust(11),
            self.account_holder_name.ljust(40)[:40],
            str(amount_paise).zfill(13),
            self.debit_date.strftime("%d%m%Y"),
            self.sponsor_bank_ifsc.ljust(11),
            self.utility_code.ljust(18),
            self.narration.ljust(30)[:30],
        ]

        return "".join(line_parts)


class NachHeaderRecord(BaseModel):
    """Header record for NACH ACH file."""

    record_type: str = Field(default="H", description="H for Header")
    file_type: str = Field(default="ACH-DR", description="File type")
    file_creation_date: date = Field(..., description="File creation date")
    file_creation_time: str = Field(..., description="File creation time HH:MM")
    sponsor_bank_ifsc: str = Field(..., max_length=11)
    utility_code: str = Field(..., max_length=18)
    batch_reference: str = Field(..., max_length=30)
    debit_date: date = Field(..., description="Debit date")
    total_count: int = Field(default=0)
    total_amount: Decimal = Field(default=Decimal("0"))

    def to_ach_line(self) -> str:
        """Convert to ACH header line."""
        amount_paise = int(self.total_amount * 100)

        line_parts = [
            self.record_type.ljust(1),
            self.file_type.ljust(10),
            self.file_creation_date.strftime("%d%m%Y"),
            self.file_creation_time.ljust(5),
            self.sponsor_bank_ifsc.ljust(11),
            self.utility_code.ljust(18),
            self.batch_reference.ljust(30),
            self.debit_date.strftime("%d%m%Y"),
            str(self.total_count).zfill(9),
            str(amount_paise).zfill(15),
        ]

        return "".join(line_parts)


class NachTrailerRecord(BaseModel):
    """Trailer record for NACH ACH file."""

    record_type: str = Field(default="T", description="T for Trailer")
    total_count: int = Field(default=0)
    total_amount: Decimal = Field(default=Decimal("0"))

    def to_ach_line(self) -> str:
        """Convert to ACH trailer line."""
        amount_paise = int(self.total_amount * 100)

        line_parts = [
            self.record_type.ljust(1),
            str(self.total_count).zfill(9),
            str(amount_paise).zfill(15),
        ]

        return "".join(line_parts)


class NachResponseRecord(BaseModel):
    """Response record from NACH response file."""

    transaction_reference: str
    umrn: str
    account_number: str
    ifsc_code: str
    amount: Decimal
    debit_date: date
    status: str  # SUCCESS, REJECTED, etc.
    return_code: str  # NPCI return code
    return_reason: Optional[str] = None
    bank_reference: Optional[str] = None
    settlement_date: Optional[date] = None

    @classmethod
    def from_ach_line(cls, line: str) -> "NachResponseRecord":
        """Parse response from ACH response file line."""
        # Parse fixed-width fields - actual format varies by provider
        return cls(
            transaction_reference=line[1:31].strip(),
            umrn=line[31:51].strip(),
            account_number=line[51:86].strip(),
            ifsc_code=line[86:97].strip(),
            amount=Decimal(line[137:150].strip()) / 100,
            debit_date=datetime.strptime(line[150:158], "%d%m%Y").date(),
            status="SUCCESS" if line[158:159] == "S" else "REJECTED",
            return_code=line[159:161].strip(),
            return_reason=line[161:261].strip() if len(line) > 161 else None,
            bank_reference=line[261:291].strip() if len(line) > 261 else None,
        )


class MandateRegistrationData(BaseModel):
    """Data for mandate registration with NPCI."""

    # Mandate reference
    mandate_reference: str = Field(..., max_length=30)

    # Account details
    account_number: str = Field(..., max_length=35)
    ifsc_code: str = Field(..., max_length=11)
    account_holder_name: str = Field(..., max_length=40)

    # Mandate details
    mandate_type: str = Field(default="N", description="N=NACH, E=eMandate")
    frequency: str = Field(default="M", description="M=Monthly, Q=Quarterly, Y=Yearly")
    first_collection_date: date
    final_collection_date: date
    max_amount: Decimal = Field(..., description="Maximum debit amount")
    amount_type: str = Field(default="F", description="F=Fixed, M=Maximum")

    # Utility details
    utility_code: str = Field(..., max_length=18)
    sponsor_bank_ifsc: str = Field(..., max_length=11)

    # Contact
    phone_number: Optional[str] = Field(None, max_length=10)
    email: Optional[str] = Field(None, max_length=50)

    def to_registration_request(self) -> dict:
        """Convert to registration API request format."""
        return {
            "mandate_reference": self.mandate_reference,
            "account_details": {
                "account_number": self.account_number,
                "ifsc": self.ifsc_code,
                "name": self.account_holder_name,
            },
            "mandate_details": {
                "type": self.mandate_type,
                "frequency": self.frequency,
                "start_date": self.first_collection_date.isoformat(),
                "end_date": self.final_collection_date.isoformat(),
                "amount": str(self.max_amount),
                "amount_type": self.amount_type,
            },
            "utility_code": self.utility_code,
            "sponsor_bank": self.sponsor_bank_ifsc,
            "contact": {
                "phone": self.phone_number,
                "email": self.email,
            }
        }


class NachApiResponse(BaseModel):
    """Standard API response from NACH providers."""

    success: bool
    request_id: str
    message: str
    data: Optional[dict] = None
    error_code: Optional[str] = None
    error_details: Optional[str] = None


class MandateStatusResponse(BaseModel):
    """Response for mandate status inquiry."""

    umrn: Optional[str] = None
    mandate_reference: str
    status: str  # PENDING, REGISTERED, ACTIVE, SUSPENDED, CANCELLED, REJECTED
    status_reason: Optional[str] = None
    registration_date: Optional[date] = None
    activation_date: Optional[date] = None


class NachReturnCodeMapping:
    """Mapping of NPCI NACH return codes to descriptions."""

    CODES = {
        "00": ("SUCCESS", "Transaction successful"),
        "01": ("INSUFFICIENT_FUNDS", "Insufficient funds in account"),
        "02": ("ACCOUNT_CLOSED", "Account closed by customer or bank"),
        "03": ("ACCOUNT_BLOCKED", "Account blocked/frozen"),
        "04": ("NO_SUCH_ACCOUNT", "No such account exists"),
        "05": ("MANDATE_NOT_FOUND", "Mandate not registered/found"),
        "06": ("MANDATE_CANCELLED", "Mandate cancelled by customer"),
        "07": ("MANDATE_EXPIRED", "Mandate expired"),
        "08": ("MANDATE_SUSPENDED", "Mandate suspended"),
        "09": ("AMOUNT_EXCEEDS_LIMIT", "Amount exceeds mandate limit"),
        "10": ("DUPLICATE_TRANSACTION", "Duplicate transaction reference"),
        "11": ("INVALID_ACCOUNT", "Invalid account number format"),
        "12": ("INVALID_IFSC", "Invalid IFSC code"),
        "13": ("BANK_REJECTED", "Rejected by destination bank"),
        "14": ("TECHNICAL_ERROR", "Technical error at bank"),
        "15": ("TIMEOUT", "Transaction timeout"),
        "99": ("OTHER", "Other/unspecified error"),
    }

    @classmethod
    def get_description(cls, code: str) -> tuple[str, str]:
        """Get enum name and description for return code."""
        return cls.CODES.get(code, ("UNKNOWN", f"Unknown code: {code}"))

    @classmethod
    def is_retryable(cls, code: str) -> bool:
        """Check if the return code indicates a retryable error."""
        retryable_codes = {"01", "14", "15"}  # Insufficient funds, technical error, timeout
        return code in retryable_codes
