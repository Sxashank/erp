"""Integration configuration service."""

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.core.encryption import encryption_service
from app.models.core.integration_config import (
    IntegrationConfig,
    IntegrationLog,
    IntegrationType,
    IntegrationProvider,
    HealthStatus,
)
from app.repositories.core.integration_config_repo import (
    IntegrationConfigRepository,
    IntegrationLogRepository,
)
from app.repositories.masters.organization_repo import OrganizationRepository
from app.schemas.core.integration_config import (
    IntegrationConfigCreate,
    IntegrationConfigUpdate,
    IntegrationTestResponse,
)


# Define sensitive fields per integration type that need encryption
SENSITIVE_FIELDS = {
    IntegrationType.NACH: [
        "api_key", "api_secret", "client_secret", "private_key_path"
    ],
    IntegrationType.ACCOUNT_AGGREGATOR: [
        "api_key", "api_secret", "client_secret"
    ],
    IntegrationType.AADHAAR_KYC: [
        "api_key", "api_secret", "client_secret", "license_key", "private_key"
    ],
    IntegrationType.PAN_VERIFICATION: [
        "api_key", "api_secret", "client_secret", "license_key"
    ],
    IntegrationType.GSTN: [
        "password", "asp_secret", "gsp_client_secret", "einvoice_password"
    ],
    IntegrationType.CREDIT_BUREAU: [
        "member_password", "api_secret", "pfx_certificate", "pfx_password"
    ],
    IntegrationType.PAYMENT_GATEWAY: [
        "api_secret", "key_secret", "webhook_secret"
    ],
    IntegrationType.SMS_GATEWAY: [
        "api_key", "auth_token"
    ],
    IntegrationType.EMAIL_GATEWAY: [
        "api_key", "api_secret"
    ],
    IntegrationType.E_INVOICE: [
        "password", "api_secret"
    ],
}


class IntegrationService:
    """Service for managing integration configurations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = IntegrationConfigRepository(session)
        self.log_repo = IntegrationLogRepository(session)
        self.org_repo = OrganizationRepository(session)

    def _get_sensitive_fields(self, integration_type: IntegrationType) -> List[str]:
        """Get list of sensitive fields for an integration type."""
        return SENSITIVE_FIELDS.get(integration_type, [])

    def _encrypt_config_data(
        self,
        config_data: Dict[str, Any],
        integration_type: IntegrationType,
    ) -> Dict[str, Any]:
        """Encrypt sensitive fields in config data."""
        sensitive_fields = self._get_sensitive_fields(integration_type)
        return encryption_service.encrypt_dict(config_data, sensitive_fields)

    def _decrypt_config_data(
        self,
        config_data: Dict[str, Any],
        integration_type: IntegrationType,
    ) -> Dict[str, Any]:
        """Decrypt sensitive fields in config data."""
        sensitive_fields = self._get_sensitive_fields(integration_type)
        return encryption_service.decrypt_dict(config_data, sensitive_fields)

    def _mask_sensitive_data(
        self,
        config_data: Dict[str, Any],
        integration_type: IntegrationType,
    ) -> Dict[str, Any]:
        """Mask sensitive fields for display (show first 4 and last 4 chars only)."""
        sensitive_fields = self._get_sensitive_fields(integration_type)
        result = config_data.copy()
        for field in sensitive_fields:
            if field in result and result[field]:
                value = str(result[field])
                if len(value) > 8:
                    result[field] = f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"
                else:
                    result[field] = "*" * len(value)
        return result

    async def create(
        self,
        data: IntegrationConfigCreate,
        created_by: Optional[UUID] = None,
    ) -> IntegrationConfig:
        """Create a new integration configuration."""
        # Verify organization exists
        org = await self.org_repo.get(data.organization_id)
        if not org:
            raise NotFoundException("Organization not found")

        # Check for duplicate
        if await self.repo.exists_for_org(
            data.organization_id,
            data.integration_type,
            data.provider,
        ):
            raise ConflictException(
                f"Integration config already exists for {data.integration_type.value}/{data.provider.value}"
            )

        # Validate provider matches integration type
        self._validate_provider_for_type(data.integration_type, data.provider)

        # Encrypt sensitive config data
        encrypted_config = self._encrypt_config_data(
            data.config_data,
            data.integration_type,
        )

        config_dict = data.model_dump()
        config_dict["config_data"] = encrypted_config
        config_dict["created_by"] = created_by
        config_dict["health_status"] = HealthStatus.UNKNOWN

        return await self.repo.create(config_dict)

    async def update(
        self,
        config_id: UUID,
        data: IntegrationConfigUpdate,
        updated_by: Optional[UUID] = None,
    ) -> IntegrationConfig:
        """Update an integration configuration."""
        config = await self.repo.get(config_id)
        if not config:
            raise NotFoundException("Integration config not found")

        update_data = data.model_dump(exclude_unset=True)

        # If config_data is being updated, merge with existing and encrypt
        if "config_data" in update_data and update_data["config_data"]:
            # Decrypt existing config
            existing_config = self._decrypt_config_data(
                config.config_data or {},
                config.integration_type,
            )
            # Merge new values
            existing_config.update(update_data["config_data"])
            # Encrypt merged config
            update_data["config_data"] = self._encrypt_config_data(
                existing_config,
                config.integration_type,
            )

        update_data["updated_by"] = updated_by
        return await self.repo.update(config, update_data)

    async def get(
        self,
        config_id: UUID,
        decrypt: bool = False,
        mask: bool = True,
    ) -> Optional[IntegrationConfig]:
        """Get an integration configuration by ID."""
        config = await self.repo.get(config_id)
        if config and decrypt:
            config.config_data = self._decrypt_config_data(
                config.config_data or {},
                config.integration_type,
            )
        elif config and mask:
            config.config_data = self._mask_sensitive_data(
                config.config_data or {},
                config.integration_type,
            )
        return config

    async def get_by_type(
        self,
        organization_id: UUID,
        integration_type: IntegrationType,
        provider: Optional[IntegrationProvider] = None,
        decrypt: bool = False,
    ) -> Optional[IntegrationConfig]:
        """Get integration config by organization and type."""
        config = await self.repo.get_by_org_and_type(
            organization_id,
            integration_type,
            provider,
        )
        if config and decrypt:
            config.config_data = self._decrypt_config_data(
                config.config_data or {},
                config.integration_type,
            )
        return config

    async def list_by_organization(
        self,
        organization_id: UUID,
        integration_type: Optional[IntegrationType] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[IntegrationConfig], int]:
        """List integration configs for an organization."""
        configs, total = await self.repo.list_by_organization(
            organization_id,
            integration_type,
            skip=skip,
            limit=limit,
        )
        # Mask sensitive data in list view
        for config in configs:
            config.config_data = self._mask_sensitive_data(
                config.config_data or {},
                config.integration_type,
            )
        return configs, total

    async def delete(
        self,
        config_id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> bool:
        """Soft delete an integration configuration."""
        config = await self.repo.get(config_id)
        if not config:
            raise NotFoundException("Integration config not found")
        await self.repo.soft_delete(config_id, deleted_by)
        return True

    async def test_connection(
        self,
        config_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> IntegrationTestResponse:
        """Test connection to an external service."""
        config = await self.repo.get(config_id)
        if not config:
            raise NotFoundException("Integration config not found")

        # Decrypt config for testing
        decrypted_config = self._decrypt_config_data(
            config.config_data or {},
            config.integration_type,
        )

        start_time = time.time()
        success = False
        message = ""
        error_code = None
        details = {}

        try:
            success, message, details = await self._test_live_connection(
                config,
                decrypted_config,
            )

        except Exception as e:
            message = str(e)
            error_code = "CONNECTION_ERROR"

        latency_ms = int((time.time() - start_time) * 1000)

        # Update health status
        health_status = HealthStatus.HEALTHY if success else HealthStatus.DOWN
        await self.repo.update_health_status(
            config_id,
            health_status,
            error_message=None if success else message,
        )

        # Log the test
        await self.log_repo.create(
            organization_id=config.organization_id,
            integration_config_id=config_id,
            integration_type=config.integration_type.value,
            provider=config.provider.value,
            endpoint="test_connection",
            method="TEST",
            is_success=success,
            error_message=None if success else message,
            latency_ms=latency_ms,
            triggered_by=user_id,
        )

        return IntegrationTestResponse(
            success=success,
            message=message,
            latency_ms=latency_ms,
            details=details if success else None,
            error_code=error_code,
        )

    async def _test_live_connection(
        self,
        config: IntegrationConfig,
        decrypted_config: Dict[str, Any],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Test a live connector only when a real client is wired.

        This intentionally fails closed. Earlier versions returned success when
        mandatory fields were present, which made fake "connected" states look
        real. Configuration can be saved, but live test/retrieval must be backed
        by a provider client before this method reports HEALTHY.
        """
        _ = decrypted_config
        return (
            False,
            (
                f"Live connection test is not implemented for "
                f"{config.integration_type.value}/{config.provider.value}. "
                "Configuration is stored, but no external API call was made."
            ),
            {},
        )

    def _validate_provider_for_type(
        self,
        integration_type: IntegrationType,
        provider: IntegrationProvider,
    ) -> None:
        """Validate that provider is valid for the integration type."""
        valid_providers = {
            IntegrationType.NACH: [
                IntegrationProvider.NPCI_DIRECT,
                IntegrationProvider.RAZORPAY_NACH,
                IntegrationProvider.CASHFREE_NACH,
                IntegrationProvider.PAYU_NACH,
            ],
            IntegrationType.ACCOUNT_AGGREGATOR: [
                IntegrationProvider.FINVU,
                IntegrationProvider.ONEMONEY,
                IntegrationProvider.SETU,
                IntegrationProvider.YODLEE,
            ],
            IntegrationType.AADHAAR_KYC: [
                IntegrationProvider.UIDAI,
                IntegrationProvider.DIGILOCKER,
                IntegrationProvider.KARZA,
                IntegrationProvider.IDFY,
            ],
            IntegrationType.PAN_VERIFICATION: [
                IntegrationProvider.NSDL_PAN,
                IntegrationProvider.PROTEAN,
                IntegrationProvider.KARZA,
                IntegrationProvider.IDFY,
            ],
            IntegrationType.GSTN: [
                IntegrationProvider.GSTN,
                IntegrationProvider.CLEARTAX,
                IntegrationProvider.ZOHO_GST,
            ],
            IntegrationType.CREDIT_BUREAU: [
                IntegrationProvider.CIBIL,
                IntegrationProvider.EXPERIAN,
                IntegrationProvider.EQUIFAX,
                IntegrationProvider.CRIF,
            ],
            IntegrationType.PAYMENT_GATEWAY: [
                IntegrationProvider.RAZORPAY,
                IntegrationProvider.CASHFREE,
                IntegrationProvider.PAYU,
                IntegrationProvider.CCAVENUE,
                IntegrationProvider.STRIPE,
            ],
            IntegrationType.SMS_GATEWAY: [
                IntegrationProvider.MSG91,
                IntegrationProvider.TWILIO,
                IntegrationProvider.TEXTLOCAL,
            ],
            IntegrationType.EMAIL_GATEWAY: [
                IntegrationProvider.SENDGRID,
                IntegrationProvider.AWS_SES,
                IntegrationProvider.MAILGUN,
            ],
            IntegrationType.E_INVOICE: [
                IntegrationProvider.NIC_EINVOICE,
                IntegrationProvider.CLEARTAX_EINVOICE,
            ],
        }

        if provider not in valid_providers.get(integration_type, []):
            raise BadRequestException(
                f"Provider {provider.value} is not valid for integration type {integration_type.value}"
            )

    # ============ Log methods ============

    async def get_logs(
        self,
        config_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[IntegrationLog], int]:
        """Get logs for a specific integration config."""
        config = await self.repo.get(config_id)
        if not config:
            raise NotFoundException("Integration config not found")
        return await self.log_repo.list_by_config(config_id, skip, limit)

    async def get_organization_logs(
        self,
        organization_id: UUID,
        integration_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        success_only: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[IntegrationLog], int]:
        """Get logs for an organization with filters."""
        return await self.log_repo.list_by_organization(
            organization_id,
            integration_type,
            from_date,
            to_date,
            success_only,
            skip,
            limit,
        )

    async def get_log_stats(
        self,
        organization_id: UUID,
        integration_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> dict:
        """Get aggregate statistics for logs."""
        return await self.log_repo.get_stats(
            organization_id,
            integration_type,
            from_date,
            to_date,
        )

    async def log_api_call(
        self,
        organization_id: UUID,
        integration_type: IntegrationType,
        provider: IntegrationProvider,
        endpoint: str,
        method: str,
        request_payload: Optional[dict] = None,
        response_payload: Optional[dict] = None,
        http_status: Optional[int] = None,
        is_success: bool = False,
        error_message: Optional[str] = None,
        latency_ms: Optional[int] = None,
        triggered_by: Optional[UUID] = None,
    ) -> IntegrationLog:
        """Log an API call to an external service."""
        # Find config for this integration
        config = await self.get_by_type(organization_id, integration_type, provider)

        # Update usage stats if config exists
        if config:
            await self.repo.update_usage_stats(config.id, is_success)

        return await self.log_repo.create(
            organization_id=organization_id,
            integration_config_id=config.id if config else None,
            integration_type=integration_type.value,
            provider=provider.value,
            endpoint=endpoint,
            method=method,
            request_payload=request_payload,
            response_payload=response_payload,
            http_status=http_status,
            is_success=is_success,
            error_message=error_message,
            latency_ms=latency_ms,
            triggered_by=triggered_by,
        )
