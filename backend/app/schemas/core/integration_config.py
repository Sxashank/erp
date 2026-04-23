"""Integration configuration schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, AuditSchema
from app.models.core.integration_config import (
    IntegrationType,
    IntegrationProvider,
    HealthStatus,
)


# ============ Provider-specific config data schemas ============


class NachConfigData(BaseSchema):
    """NACH integration configuration data."""

    # Common NACH fields
    merchant_id: Optional[str] = Field(None, description="Merchant/Corporate ID")
    sponsor_bank_code: Optional[str] = Field(None, description="Sponsor bank IFSC")
    utility_code: Optional[str] = Field(None, description="NPCI Utility Code")

    # API credentials
    api_key: Optional[str] = Field(None, description="API Key")
    api_secret: Optional[str] = Field(None, description="API Secret")
    client_id: Optional[str] = Field(None, description="Client ID")
    client_secret: Optional[str] = Field(None, description="Client Secret")

    # Certificate paths (for NPCI direct)
    certificate_path: Optional[str] = Field(None, description="Path to SSL certificate")
    private_key_path: Optional[str] = Field(None, description="Path to private key")

    # Callback URLs
    mandate_callback_url: Optional[str] = Field(None, description="Mandate status callback")
    debit_callback_url: Optional[str] = Field(None, description="Debit status callback")


class AccountAggregatorConfigData(BaseSchema):
    """Account Aggregator integration configuration data."""

    # FIU (Financial Information User) credentials
    fiu_id: Optional[str] = Field(None, description="FIU Entity ID")
    api_key: Optional[str] = Field(None, description="API Key")
    api_secret: Optional[str] = Field(None, description="API Secret")

    # AA specific
    aa_id: Optional[str] = Field(None, description="Account Aggregator ID")
    client_id: Optional[str] = Field(None, description="Client ID")
    client_secret: Optional[str] = Field(None, description="Client Secret")

    # Token endpoint
    token_url: Optional[str] = Field(None, description="Token endpoint URL")

    # FI types to request
    default_fi_types: List[str] = Field(
        default=["DEPOSIT", "RECURRING_DEPOSIT"],
        description="Default FI types to request"
    )

    # Consent template
    consent_template_id: Optional[str] = Field(None, description="Default consent template")


class GstnConfigData(BaseSchema):
    """GSTN portal integration configuration data."""

    # GSTN credentials
    gstin: Optional[str] = Field(None, description="Primary GSTIN")
    username: Optional[str] = Field(None, description="GSTN portal username")
    password: Optional[str] = Field(None, description="GSTN portal password (encrypted)")

    # ASP/GSP credentials (for API access)
    asp_id: Optional[str] = Field(None, description="ASP ID")
    asp_secret: Optional[str] = Field(None, description="ASP Secret")
    gsp_client_id: Optional[str] = Field(None, description="GSP Client ID")
    gsp_client_secret: Optional[str] = Field(None, description="GSP Client Secret")

    # E-Invoice settings
    einvoice_username: Optional[str] = Field(None, description="E-Invoice portal username")
    einvoice_password: Optional[str] = Field(None, description="E-Invoice portal password")

    # Auto-filing settings
    auto_file_gstr1: bool = Field(default=False, description="Auto-file GSTR-1")
    auto_file_gstr3b: bool = Field(default=False, description="Auto-file GSTR-3B")


class CreditBureauConfigData(BaseSchema):
    """Credit bureau integration configuration data."""

    # Bureau credentials
    member_id: Optional[str] = Field(None, description="Bureau member ID")
    member_password: Optional[str] = Field(None, description="Bureau password")
    user_id: Optional[str] = Field(None, description="User ID for API access")

    # API credentials
    api_key: Optional[str] = Field(None, description="API Key")
    api_secret: Optional[str] = Field(None, description="API Secret")

    # Inquiry settings
    default_inquiry_type: str = Field(default="SOFT", description="Default inquiry type")
    purpose_code: Optional[str] = Field(None, description="Purpose code for pulls")

    # Certificate (for CIBIL)
    pfx_certificate: Optional[str] = Field(None, description="PFX certificate base64")
    pfx_password: Optional[str] = Field(None, description="PFX certificate password")


class PaymentGatewayConfigData(BaseSchema):
    """Payment gateway integration configuration data."""

    # Merchant credentials
    merchant_id: Optional[str] = Field(None, description="Merchant ID")
    api_key: Optional[str] = Field(None, description="API Key")
    api_secret: Optional[str] = Field(None, description="API Secret / Key Secret")

    # For Razorpay
    key_id: Optional[str] = Field(None, description="Razorpay Key ID")
    key_secret: Optional[str] = Field(None, description="Razorpay Key Secret")

    # Webhook
    webhook_secret: Optional[str] = Field(None, description="Webhook verification secret")

    # Payment page settings
    payment_page_name: Optional[str] = Field(None, description="Payment page display name")
    theme_color: Optional[str] = Field(None, description="Theme color hex")
    logo_url: Optional[str] = Field(None, description="Logo URL for payment page")

    # Settlement
    settlement_account: Optional[str] = Field(None, description="Settlement bank account")


# ============ Integration Config CRUD schemas ============


class IntegrationConfigCreate(BaseSchema):
    """Schema for creating an integration configuration."""

    organization_id: UUID
    integration_type: IntegrationType
    provider: IntegrationProvider
    display_name: Optional[str] = Field(None, max_length=100)
    config_data: Dict[str, Any] = Field(default_factory=dict)
    sandbox_mode: bool = True
    base_url: Optional[str] = Field(None, max_length=500)
    sandbox_url: Optional[str] = Field(None, max_length=500)
    webhook_url: Optional[str] = Field(None, max_length=500)
    webhook_secret: Optional[str] = Field(None, max_length=255)

    @field_validator("integration_type", "provider", mode="before")
    @classmethod
    def validate_enums(cls, v):
        """Allow string values for enums."""
        if isinstance(v, str):
            return v
        return v


class IntegrationConfigUpdate(BaseSchema):
    """Schema for updating an integration configuration."""

    display_name: Optional[str] = Field(None, max_length=100)
    config_data: Optional[Dict[str, Any]] = None
    sandbox_mode: Optional[bool] = None
    base_url: Optional[str] = Field(None, max_length=500)
    sandbox_url: Optional[str] = Field(None, max_length=500)
    webhook_url: Optional[str] = Field(None, max_length=500)
    webhook_secret: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class IntegrationConfigResponse(AuditSchema):
    """Integration configuration response schema."""

    id: UUID
    organization_id: UUID
    integration_type: IntegrationType
    provider: IntegrationProvider
    display_name: Optional[str] = None
    config_data: Dict[str, Any] = Field(default_factory=dict)
    sandbox_mode: bool
    base_url: Optional[str] = None
    sandbox_url: Optional[str] = None
    webhook_url: Optional[str] = None
    # Note: webhook_secret is not returned for security
    last_health_check: Optional[datetime] = None
    health_status: HealthStatus
    last_error_message: Optional[str] = None
    last_used_at: Optional[datetime] = None
    total_requests: int = 0
    failed_requests: int = 0


class IntegrationConfigListResponse(BaseSchema):
    """Simplified integration config for list views."""

    id: UUID
    integration_type: IntegrationType
    provider: IntegrationProvider
    display_name: Optional[str] = None
    sandbox_mode: bool
    is_active: bool
    health_status: HealthStatus
    last_used_at: Optional[datetime] = None


# ============ Integration Log schemas ============


class IntegrationLogResponse(BaseSchema):
    """Integration log response schema."""

    id: UUID
    organization_id: UUID
    integration_type: str
    provider: str
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    request_payload: Optional[Dict[str, Any]] = None
    response_payload: Optional[Dict[str, Any]] = None
    http_status: Optional[int] = None
    is_success: bool
    error_message: Optional[str] = None
    latency_ms: Optional[int] = None
    created_at: datetime
    triggered_by: Optional[UUID] = None


# ============ Test Connection schemas ============


class IntegrationTestRequest(BaseSchema):
    """Request schema for testing integration connection."""

    # Optional: test with provided config instead of saved
    config_data: Optional[Dict[str, Any]] = None
    sandbox_mode: Optional[bool] = None


class IntegrationTestResponse(BaseSchema):
    """Response schema for integration test."""

    success: bool
    message: str
    latency_ms: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None


# ============ Bulk operations schemas ============


class IntegrationConfigBulkResponse(BaseSchema):
    """Response for bulk integration config operations."""

    configs: Dict[str, Optional[IntegrationConfigListResponse]] = Field(
        description="Config by integration type"
    )
    available_types: List[str] = Field(
        description="All available integration types"
    )


# ============ Config template schemas ============


class IntegrationConfigTemplate(BaseSchema):
    """Template showing required fields for an integration type."""

    integration_type: IntegrationType
    provider: IntegrationProvider
    required_fields: List[str]
    optional_fields: List[str]
    description: str
    documentation_url: Optional[str] = None
