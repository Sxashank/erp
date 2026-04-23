"""Base classes for eSign providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID


class ESignStatus(str, Enum):
    """eSign request status."""
    INITIATED = "INITIATED"
    OTP_SENT = "OTP_SENT"
    OTP_VERIFIED = "OTP_VERIFIED"
    SIGNING = "SIGNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class SignerType(str, Enum):
    """Type of signer."""
    INDIVIDUAL = "INDIVIDUAL"
    COMPANY = "COMPANY"
    AUTHORIZED_SIGNATORY = "AUTHORIZED_SIGNATORY"


class AuthMode(str, Enum):
    """Authentication mode for eSign."""
    AADHAAR_OTP = "AADHAAR_OTP"
    AADHAAR_BIOMETRIC = "AADHAAR_BIOMETRIC"
    PAN_AADHAAR = "PAN_AADHAAR"
    DSC = "DSC"


@dataclass
class Signer:
    """Document signer details."""
    name: str
    email: str
    phone: str
    aadhaar_number: Optional[str] = None
    pan_number: Optional[str] = None
    signer_type: SignerType = SignerType.INDIVIDUAL
    auth_mode: AuthMode = AuthMode.AADHAAR_OTP
    sign_positions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ESignRequest:
    """eSign request."""
    document_id: str
    document_name: str
    document_path: str  # Path to PDF file
    signers: List[Signer]
    # Request metadata
    organization_id: Optional[UUID] = None
    entity_type: Optional[str] = None  # loan_agreement, noc, etc.
    entity_id: Optional[UUID] = None
    # Options
    expiry_hours: int = 72  # Default 3 days
    sequential_signing: bool = False
    callback_url: Optional[str] = None
    redirect_url: Optional[str] = None
    send_notifications: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ESignResponse:
    """eSign response."""
    success: bool
    request_id: Optional[str] = None
    provider_request_id: Optional[str] = None
    status: ESignStatus = ESignStatus.INITIATED
    signing_url: Optional[str] = None  # URL for signer to sign
    signed_document_path: Optional[str] = None
    signed_document_url: Optional[str] = None
    signers_status: List[Dict[str, Any]] = field(default_factory=list)
    certificate_info: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ESignError(Exception):
    """eSign error."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.provider = provider
        self.details = details or {}


class ESignProvider(ABC):
    """Abstract base class for eSign providers."""

    provider_name: str = "base"

    def __init__(self, config: Dict[str, Any]):
        """Initialize provider."""
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider configuration."""
        pass

    @abstractmethod
    async def initiate_signing(self, request: ESignRequest) -> ESignResponse:
        """Initiate document signing request."""
        pass

    @abstractmethod
    async def send_otp(self, request_id: str, signer_id: str) -> bool:
        """Send OTP to signer."""
        pass

    @abstractmethod
    async def verify_otp(
        self, request_id: str, signer_id: str, otp: str
    ) -> ESignResponse:
        """Verify OTP and complete signing."""
        pass

    @abstractmethod
    async def get_status(self, request_id: str) -> ESignResponse:
        """Get signing request status."""
        pass

    @abstractmethod
    async def download_signed_document(
        self, request_id: str
    ) -> Optional[bytes]:
        """Download signed document."""
        pass

    @abstractmethod
    async def cancel_request(self, request_id: str) -> bool:
        """Cancel signing request."""
        pass

    @abstractmethod
    async def verify_webhook_signature(
        self, payload: bytes, signature: str
    ) -> bool:
        """Verify webhook signature."""
        pass
