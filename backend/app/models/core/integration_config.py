"""Integration configuration models for external service connections."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization


class IntegrationType(str, enum.Enum):
    """Types of external integrations."""

    NACH = "NACH"
    ACCOUNT_AGGREGATOR = "ACCOUNT_AGGREGATOR"
    GSTN = "GSTN"
    CREDIT_BUREAU = "CREDIT_BUREAU"
    PAYMENT_GATEWAY = "PAYMENT_GATEWAY"
    SMS_GATEWAY = "SMS_GATEWAY"
    EMAIL_GATEWAY = "EMAIL_GATEWAY"
    E_INVOICE = "E_INVOICE"


class IntegrationProvider(str, enum.Enum):
    """External service providers."""

    # NACH Providers
    NPCI_DIRECT = "NPCI_DIRECT"
    RAZORPAY_NACH = "RAZORPAY_NACH"
    CASHFREE_NACH = "CASHFREE_NACH"
    PAYU_NACH = "PAYU_NACH"

    # Account Aggregator Providers
    FINVU = "FINVU"
    ONEMONEY = "ONEMONEY"
    SETU = "SETU"
    YODLEE = "YODLEE"

    # GSTN Provider
    GSTN = "GSTN"
    CLEARTAX = "CLEARTAX"
    ZOHO_GST = "ZOHO_GST"

    # Credit Bureau Providers
    CIBIL = "CIBIL"
    EXPERIAN = "EXPERIAN"
    EQUIFAX = "EQUIFAX"
    CRIF = "CRIF"

    # Payment Gateway Providers
    RAZORPAY = "RAZORPAY"
    CASHFREE = "CASHFREE"
    PAYU = "PAYU"
    CCAVENUE = "CCAVENUE"
    STRIPE = "STRIPE"
    PAYTM = "PAYTM"

    # SMS Providers
    MSG91 = "MSG91"
    TWILIO = "TWILIO"
    TEXTLOCAL = "TEXTLOCAL"

    # Email Providers
    SENDGRID = "SENDGRID"
    AWS_SES = "AWS_SES"
    MAILGUN = "MAILGUN"

    # E-Invoice Providers
    NIC_EINVOICE = "NIC_EINVOICE"
    CLEARTAX_EINVOICE = "CLEARTAX_EINVOICE"


class HealthStatus(str, enum.Enum):
    """Health status of integration."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"
    UNKNOWN = "UNKNOWN"


class IntegrationConfig(BaseModel):
    """
    Integration configuration for external services.

    Stores tenant-specific API credentials and settings for external integrations.
    Credentials are encrypted at rest using Fernet encryption.
    """

    __tablename__ = "sys_integration_config"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "integration_type",
            "provider",
            name="uq_integration_org_type_provider",
        ),
    )

    # Organization relationship
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Integration identification
    integration_type: Mapped[IntegrationType] = mapped_column(
        Enum(IntegrationType),
        nullable=False,
        index=True,
    )
    provider: Mapped[IntegrationProvider] = mapped_column(
        Enum(IntegrationProvider),
        nullable=False,
    )

    # Display name for UI
    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Configuration data (encrypted JSON)
    # Contains: api_key, api_secret, merchant_id, client_id, client_secret, etc.
    config_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Environment settings
    sandbox_mode: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    base_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    sandbox_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Webhook configuration
    webhook_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    webhook_secret: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Health monitoring
    last_health_check: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    health_status: Mapped[HealthStatus] = mapped_column(
        Enum(HealthStatus),
        default=HealthStatus.UNKNOWN,
        nullable=False,
    )
    last_error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Usage tracking
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    total_requests: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    failed_requests: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="integration_configs",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<IntegrationConfig(org={self.organization_id}, type={self.integration_type}, provider={self.provider})>"


class IntegrationLog(Base):
    """
    Log of all API calls made through integrations.

    Used for debugging, audit trail, and analytics.
    """

    __tablename__ = "sys_integration_log"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    # Organization reference
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Integration reference (optional - may be deleted)
    integration_config_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sys_integration_config.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Integration identification (denormalized for log retention)
    integration_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Request details
    request_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    endpoint: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    method: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )
    request_payload: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Response details
    response_payload: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    http_status: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    is_success: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Performance
    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # User who triggered the request (optional)
    triggered_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    integration_config: Mapped[Optional["IntegrationConfig"]] = relationship(
        "IntegrationConfig",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<IntegrationLog(id={self.id}, type={self.integration_type}, status={self.http_status})>"
