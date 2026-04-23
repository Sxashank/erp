"""Schemas for Account Aggregator integration API requests/responses."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AAConsentRequest(BaseModel):
    """Request for creating a consent request."""
    customer_vua: str = Field(..., description="Virtual User Address (e.g., user@finvu)")
    purpose: str = Field(default="102", description="Purpose code as per AA spec")
    purpose_description: Optional[str] = None
    fi_types: List[str] = Field(default=["DEPOSIT"], description="Financial Information types")
    consent_mode: str = Field(default="VIEW")
    fetch_type: str = Field(default="ONETIME")  # ONETIME, PERIODIC
    data_range_from: date
    data_range_to: date
    consent_validity_months: int = Field(default=6, ge=1, le=24)
    data_life_months: int = Field(default=6, ge=1, le=24)
    redirect_url: Optional[str] = None
    # FIU details
    fiu_entity_id: str
    # Metadata
    customer_id: Optional[str] = None  # Internal reference
    loan_application_id: Optional[str] = None
    loan_account_id: Optional[str] = None


class AAConsentResponse(BaseModel):
    """Response from consent request."""
    success: bool
    consent_handle: Optional[str] = None
    consent_id: Optional[str] = None
    consent_status: str = "PENDING"
    redirect_url: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class AAFetchRequest(BaseModel):
    """Request to fetch financial data."""
    consent_id: str
    session_id: Optional[str] = None
    fi_types: Optional[List[str]] = None  # None = all approved types
    data_range_from: Optional[date] = None
    data_range_to: Optional[date] = None


class AAFetchResponse(BaseModel):
    """Response from data fetch."""
    success: bool
    session_id: Optional[str] = None
    data_session_id: Optional[str] = None
    status: str = "INITIATED"
    fi_data: Optional[List["AAFIData"]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class AAFIData(BaseModel):
    """Financial Information data from AA."""
    fi_type: str  # DEPOSIT, TERM_DEPOSIT, etc.
    fip_id: str  # Financial Information Provider ID
    link_ref_number: Optional[str] = None
    masked_account_number: Optional[str] = None
    account_type: Optional[str] = None  # SAVINGS, CURRENT
    # Profile data
    profile: Optional[Dict[str, Any]] = None
    # Summary data
    summary: Optional[Dict[str, Any]] = None
    # Transaction data
    transactions: Optional[List[Dict[str, Any]]] = None
    # Raw decrypted data
    raw_data: Optional[Dict[str, Any]] = None


class AANotification(BaseModel):
    """Webhook notification from AA."""
    notification_type: str  # CONSENT_STATUS, FI_NOTIFICATION, SESSION_STATUS
    timestamp: datetime
    consent_handle: Optional[str] = None
    consent_id: Optional[str] = None
    session_id: Optional[str] = None
    status: Optional[str] = None
    # For FI notification
    fi_status_response: Optional[List[Dict[str, Any]]] = None
    # Raw payload
    payload: Dict[str, Any]


class AAConsentStatusUpdate(BaseModel):
    """Consent status update from webhook."""
    consent_handle: str
    consent_id: Optional[str] = None
    status: str  # ACTIVE, REJECTED, REVOKED, PAUSED, EXPIRED
    reason: Optional[str] = None
    timestamp: datetime


class AAFIStatusResponse(BaseModel):
    """FI status response item."""
    fip_id: str
    link_ref_number: str
    status: str  # READY, DENIED, PENDING, TIMEOUT
    fi_type: Optional[str] = None


class AADataDecryptRequest(BaseModel):
    """Request to decrypt FI data."""
    base64_data: str
    base64_nonce: str
    key_material_nonce: str
    fip_key_material: Dict[str, str]


class AAHealthCheckResponse(BaseModel):
    """Health check response."""
    is_healthy: bool
    provider: str
    response_time_ms: Optional[int] = None
    timestamp: datetime
    error_message: Optional[str] = None


class AAKeyMaterial(BaseModel):
    """Key material for encryption/decryption."""
    cryptoAlg: str = "ECDH"
    curve: str = "Curve25519"
    params: str = "AESGCM"
    DHPublicKey: Dict[str, str]
    Nonce: str


class AASignedConsent(BaseModel):
    """Digitally signed consent artifact."""
    consent_id: str
    consent_handle: str
    customer_vua: str
    fiu_id: str
    fi_types: List[str]
    consent_start: datetime
    consent_expiry: datetime
    consent_mode: str
    fetch_type: str
    data_filter: Optional[Dict[str, Any]] = None
    signature: str


# Update forward references
AAFetchResponse.model_rebuild()
