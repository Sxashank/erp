"""Integration configuration API endpoints."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_with_tenant
from app.models.auth.user import User
from app.models.core.integration_config import IntegrationType, IntegrationProvider
from app.services.core.integration_service import IntegrationService
from app.schemas.core.integration_config import (
    IntegrationConfigCreate,
    IntegrationConfigUpdate,
    IntegrationConfigResponse,
    IntegrationConfigListResponse,
    IntegrationLogResponse,
    IntegrationTestResponse,
    IntegrationConfigTemplate,
)
from app.schemas.base import MessageResponse
from app.core.responses import PaginatedResponse as PaginatedResponseModel
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/integrations", tags=["Integrations"])


# ============ Integration Config CRUD ============


@router.get(
    "",
    response_model=PaginatedResponseModel[IntegrationConfigListResponse], response_model_by_alias=True,
    summary="List integration configurations",
)
async def list_integrations(
    integration_type: Optional[IntegrationType] = Query(
        None,
        alias="integrationType",
        description="Filter by type",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, alias="pageSize", ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> PaginatedResponseModel[IntegrationConfigListResponse]:
    """
    List all integration configurations for an organization.
    """
    service = IntegrationService(db)
    skip = (page - 1) * page_size

    configs, total = await service.list_by_organization(
        current_user.organization_id,
        integration_type,
        skip=skip,
        limit=page_size,
    )

    items = [
        IntegrationConfigListResponse(
            id=c.id,
            integration_type=c.integration_type,
            provider=c.provider,
            display_name=c.display_name,
            sandbox_mode=c.sandbox_mode,
            is_active=c.is_active,
            health_status=c.health_status,
            last_used_at=c.last_used_at,
        )
        for c in configs
    ]

    return PaginatedResponseModel.create(items, total, page, page_size)


@router.post(
    "",
    response_model=IntegrationConfigResponse, response_model_by_alias=True,
    summary="Create integration configuration",
)
async def create_integration(
    data: IntegrationConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> IntegrationConfigResponse:
    """
    Create a new integration configuration.

    Config data should contain credentials specific to the integration type:
    - NACH: api_key, api_secret, merchant_id, utility_code
    - ACCOUNT_AGGREGATOR: fiu_id, api_key, api_secret, client_id
    - GSTN: gstin, username, password, asp_id, asp_secret
    - CREDIT_BUREAU: member_id, member_password, api_key
    - PAYMENT_GATEWAY: merchant_id, api_key, api_secret (or key_id/key_secret for Razorpay)
    """
    service = IntegrationService(db)
    # Force tenant scope from the JWT — never trust the request body for org scope.
    scoped_data = data.model_copy(update={"organization_id": current_user.organization_id})
    config = await service.create(scoped_data, current_user.id)

    return IntegrationConfigResponse.model_validate(config)


@router.get(
    "/types",
    response_model=List[dict], response_model_by_alias=True,
    summary="List available integration types",
)
async def list_integration_types(
    current_user: User = Depends(get_current_user),
) -> List[dict]:
    """
    List all available integration types and their providers.
    """
    return [
        {
            "type": IntegrationType.NACH.value,
            "label": "NACH / eNACH",
            "description": "Auto-debit EMI collection via NPCI NACH",
            "providers": [
                {"value": p.value, "label": _get_provider_label(p)}
                for p in [
                    IntegrationProvider.NPCI_DIRECT,
                    IntegrationProvider.RAZORPAY_NACH,
                    IntegrationProvider.CASHFREE_NACH,
                ]
            ],
        },
        {
            "type": IntegrationType.ACCOUNT_AGGREGATOR.value,
            "label": "Account Aggregator",
            "description": "Auto-fetch bank statements via AA framework",
            "providers": [
                {"value": p.value, "label": _get_provider_label(p)}
                for p in [
                    IntegrationProvider.FINVU,
                    IntegrationProvider.ONEMONEY,
                    IntegrationProvider.SETU,
                ]
            ],
        },
        {
            "type": IntegrationType.AADHAAR_KYC.value,
            "label": "Aadhaar KYC",
            "description": "Aadhaar XML/eKYC verification through approved providers",
            "providers": [
                {"value": p.value, "label": _get_provider_label(p)}
                for p in [
                    IntegrationProvider.UIDAI,
                    IntegrationProvider.DIGILOCKER,
                    IntegrationProvider.KARZA,
                    IntegrationProvider.IDFY,
                ]
            ],
        },
        {
            "type": IntegrationType.PAN_VERIFICATION.value,
            "label": "PAN Verification",
            "description": "PAN validation and name/status verification",
            "providers": [
                {"value": p.value, "label": _get_provider_label(p)}
                for p in [
                    IntegrationProvider.NSDL_PAN,
                    IntegrationProvider.PROTEAN,
                    IntegrationProvider.KARZA,
                    IntegrationProvider.IDFY,
                ]
            ],
        },
        {
            "type": IntegrationType.GSTN.value,
            "label": "GSTN Portal",
            "description": "GST return filing and ITC reconciliation",
            "providers": [
                {"value": p.value, "label": _get_provider_label(p)}
                for p in [
                    IntegrationProvider.GSTN,
                    IntegrationProvider.CLEARTAX,
                ]
            ],
        },
        {
            "type": IntegrationType.CREDIT_BUREAU.value,
            "label": "Credit Bureau",
            "description": "Credit score pulls for loan underwriting",
            "providers": [
                {"value": p.value, "label": _get_provider_label(p)}
                for p in [
                    IntegrationProvider.CIBIL,
                    IntegrationProvider.EXPERIAN,
                    IntegrationProvider.EQUIFAX,
                ]
            ],
        },
        {
            "type": IntegrationType.PAYMENT_GATEWAY.value,
            "label": "Payment Gateway",
            "description": "Online payment collection",
            "providers": [
                {"value": p.value, "label": _get_provider_label(p)}
                for p in [
                    IntegrationProvider.RAZORPAY,
                    IntegrationProvider.CASHFREE,
                    IntegrationProvider.PAYU,
                ]
            ],
        },
        {
            "type": IntegrationType.SMS_GATEWAY.value,
            "label": "SMS Gateway",
            "description": "OTP, alerts, reminders, and borrower/employee notifications",
            "providers": [
                {"value": p.value, "label": _get_provider_label(p)}
                for p in [
                    IntegrationProvider.MSG91,
                    IntegrationProvider.TWILIO,
                    IntegrationProvider.TEXTLOCAL,
                ]
            ],
        },
        {
            "type": IntegrationType.EMAIL_GATEWAY.value,
            "label": "Email Gateway",
            "description": "Transactional email, reports, certificates, and notification delivery",
            "providers": [
                {"value": p.value, "label": _get_provider_label(p)}
                for p in [
                    IntegrationProvider.SENDGRID,
                    IntegrationProvider.AWS_SES,
                    IntegrationProvider.MAILGUN,
                ]
            ],
        },
        {
            "type": IntegrationType.E_INVOICE.value,
            "label": "E-Invoice / E-Way Bill",
            "description": "Invoice reference and e-way bill API configuration",
            "providers": [
                {"value": p.value, "label": _get_provider_label(p)}
                for p in [
                    IntegrationProvider.NIC_EINVOICE,
                    IntegrationProvider.CLEARTAX_EINVOICE,
                ]
            ],
        },
    ]


def _get_provider_label(provider: IntegrationProvider) -> str:
    """Get human-readable label for provider."""
    labels = {
        IntegrationProvider.NPCI_DIRECT: "NPCI Direct",
        IntegrationProvider.RAZORPAY_NACH: "Razorpay NACH",
        IntegrationProvider.CASHFREE_NACH: "Cashfree NACH",
        IntegrationProvider.FINVU: "Finvu",
        IntegrationProvider.ONEMONEY: "OneMoney",
        IntegrationProvider.SETU: "Setu",
        IntegrationProvider.YODLEE: "Yodlee",
        IntegrationProvider.UIDAI: "UIDAI",
        IntegrationProvider.DIGILOCKER: "DigiLocker",
        IntegrationProvider.KARZA: "Karza",
        IntegrationProvider.IDFY: "IDfy",
        IntegrationProvider.NSDL_PAN: "NSDL PAN",
        IntegrationProvider.PROTEAN: "Protean",
        IntegrationProvider.GSTN: "GSTN Direct",
        IntegrationProvider.CLEARTAX: "ClearTax",
        IntegrationProvider.ZOHO_GST: "Zoho GST",
        IntegrationProvider.CIBIL: "CIBIL",
        IntegrationProvider.EXPERIAN: "Experian",
        IntegrationProvider.EQUIFAX: "Equifax",
        IntegrationProvider.CRIF: "CRIF",
        IntegrationProvider.RAZORPAY: "Razorpay",
        IntegrationProvider.CASHFREE: "Cashfree",
        IntegrationProvider.PAYU: "PayU",
        IntegrationProvider.CCAVENUE: "CCAvenue",
        IntegrationProvider.STRIPE: "Stripe",
        IntegrationProvider.PAYTM: "Paytm",
        IntegrationProvider.MSG91: "MSG91",
        IntegrationProvider.TWILIO: "Twilio",
        IntegrationProvider.TEXTLOCAL: "Textlocal",
        IntegrationProvider.SENDGRID: "SendGrid",
        IntegrationProvider.AWS_SES: "AWS SES",
        IntegrationProvider.MAILGUN: "Mailgun",
        IntegrationProvider.NIC_EINVOICE: "NIC e-Invoice",
        IntegrationProvider.CLEARTAX_EINVOICE: "ClearTax e-Invoice",
    }
    return labels.get(provider, provider.value)


@router.get(
    "/by-type/{integration_type}",
    response_model=Optional[IntegrationConfigResponse], response_model_by_alias=True,
    summary="Get integration by type",
)
async def get_integration_by_type(
    integration_type: IntegrationType,
    provider: Optional[IntegrationProvider] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> Optional[IntegrationConfigResponse]:
    """
    Get integration configuration by type for an organization.
    Returns null if not configured.
    """
    service = IntegrationService(db)
    config = await service.get_by_type(current_user.organization_id, integration_type, provider)

    if not config:
        return None

    return IntegrationConfigResponse.model_validate(config)


@router.get(
    "/{config_id}",
    response_model=IntegrationConfigResponse, response_model_by_alias=True,
    summary="Get integration configuration",
)
async def get_integration(
    config_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> IntegrationConfigResponse:
    """
    Get a specific integration configuration by ID.
    Sensitive fields are masked.
    """
    service = IntegrationService(db)
    config = await service.get(config_id, decrypt=False, mask=True)

    if not config:
        raise NotFoundException(
            detail="Integration config not found",
            error_code="INTEGRATION_CONFIG_NOT_FOUND",
        )

    return IntegrationConfigResponse.model_validate(config)


@router.put(
    "/{config_id}",
    response_model=IntegrationConfigResponse, response_model_by_alias=True,
    summary="Update integration configuration",
)
async def update_integration(
    config_id: UUID,
    data: IntegrationConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> IntegrationConfigResponse:
    """
    Update an existing integration configuration.
    Config data is merged with existing values.
    """
    service = IntegrationService(db)
    config = await service.update(config_id, data, current_user.id)

    return IntegrationConfigResponse.model_validate(config)


@router.delete(
    "/{config_id}",
    response_model=MessageResponse, response_model_by_alias=True,
    summary="Delete integration configuration",
)
async def delete_integration(
    config_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> MessageResponse:
    """
    Soft delete an integration configuration.
    """
    service = IntegrationService(db)
    await service.delete(config_id, current_user.id)

    return MessageResponse(message="Integration configuration deleted successfully")


# ============ Test Connection ============


@router.post(
    "/{config_id}/test",
    response_model=IntegrationTestResponse, response_model_by_alias=True,
    summary="Test integration connection",
)
async def test_integration(
    config_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> IntegrationTestResponse:
    """
    Test the connection to an external service.
    Updates health status based on result.
    """
    service = IntegrationService(db)
    return await service.test_connection(config_id, current_user.id)


# ============ Integration Logs ============


@router.get(
    "/{config_id}/logs",
    response_model=PaginatedResponseModel[IntegrationLogResponse], response_model_by_alias=True,
    summary="Get integration logs",
)
async def get_integration_logs(
    config_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, alias="pageSize", ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> PaginatedResponseModel[IntegrationLogResponse]:
    """
    Get API call logs for a specific integration.
    """
    service = IntegrationService(db)
    skip = (page - 1) * page_size

    logs, total = await service.get_logs(config_id, skip, page_size)

    items = [IntegrationLogResponse.model_validate(log) for log in logs]

    return PaginatedResponseModel.create(items, total, page, page_size)


@router.get(
    "/logs/organization",
    response_model=PaginatedResponseModel[IntegrationLogResponse], response_model_by_alias=True,
    summary="Get organization integration logs",
)
async def get_organization_logs(
    integration_type: Optional[str] = Query(None, alias="integrationType"),
    from_date: Optional[datetime] = Query(None, alias="fromDate"),
    to_date: Optional[datetime] = Query(None, alias="toDate"),
    success_only: Optional[bool] = Query(None, alias="successOnly"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, alias="pageSize", ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> PaginatedResponseModel[IntegrationLogResponse]:
    """
    Get all integration logs for an organization.
    """
    service = IntegrationService(db)
    skip = (page - 1) * page_size

    logs, total = await service.get_organization_logs(
        current_user.organization_id,
        integration_type,
        from_date,
        to_date,
        success_only,
        skip,
        page_size,
    )

    items = [IntegrationLogResponse.model_validate(log) for log in logs]

    return PaginatedResponseModel.create(items, total, page, page_size)


@router.get(
    "/logs/stats",
    summary="Get integration log statistics",
)
async def get_log_stats(
    integration_type: Optional[str] = Query(None, alias="integrationType"),
    from_date: Optional[datetime] = Query(None, alias="fromDate"),
    to_date: Optional[datetime] = Query(None, alias="toDate"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> dict:
    """
    Get aggregate statistics for integration API calls.
    """
    service = IntegrationService(db)
    return await service.get_log_stats(
        current_user.organization_id,
        integration_type,
        from_date,
        to_date,
    )


# ============ Config Templates ============


@router.get(
    "/templates/{integration_type}",
    response_model=IntegrationConfigTemplate, response_model_by_alias=True,
    summary="Get configuration template",
)
async def get_config_template(
    integration_type: IntegrationType,
    provider: IntegrationProvider = Query(...),
    current_user: User = Depends(get_current_user),
) -> IntegrationConfigTemplate:
    """
    Get a template showing required and optional fields for an integration.
    """
    templates = {
        (IntegrationType.NACH, IntegrationProvider.RAZORPAY_NACH): {
            "required_fields": ["key_id", "key_secret"],
            "optional_fields": ["webhook_secret", "merchant_name"],
            "description": "Razorpay NACH requires Key ID and Key Secret from dashboard",
            "documentation_url": "https://razorpay.com/docs/recurring-payments/",
        },
        (IntegrationType.NACH, IntegrationProvider.NPCI_DIRECT): {
            "required_fields": ["merchant_id", "sponsor_bank_code", "utility_code", "certificate_path"],
            "optional_fields": ["private_key_path"],
            "description": "Direct NPCI integration requires merchant registration with NPCI",
            "documentation_url": "https://www.npci.org.in/what-we-do/nach/product-overview",
        },
        (IntegrationType.ACCOUNT_AGGREGATOR, IntegrationProvider.FINVU): {
            "required_fields": ["fiu_id", "api_key", "api_secret"],
            "optional_fields": ["default_fi_types", "consent_template_id"],
            "description": "Finvu Account Aggregator for bank statement fetching",
            "documentation_url": "https://finvu.in/docs",
        },
        (IntegrationType.ACCOUNT_AGGREGATOR, IntegrationProvider.SETU): {
            "required_fields": ["client_id", "client_secret"],
            "optional_fields": ["default_fi_types"],
            "description": "Setu Account Aggregator integration",
            "documentation_url": "https://docs.setu.co/data/account-aggregator",
        },
        (IntegrationType.AADHAAR_KYC, IntegrationProvider.UIDAI): {
            "required_fields": ["client_id", "client_secret"],
            "optional_fields": ["redirect_url", "private_key"],
            "description": "Aadhaar eKYC configuration. Live retrieval requires an approved UIDAI/KUA integration.",
            "documentation_url": None,
        },
        (IntegrationType.AADHAAR_KYC, IntegrationProvider.DIGILOCKER): {
            "required_fields": ["client_id", "client_secret", "redirect_url"],
            "optional_fields": ["api_key"],
            "description": "DigiLocker Aadhaar document fetch configuration.",
            "documentation_url": "https://www.digilocker.gov.in/developer",
        },
        (IntegrationType.AADHAAR_KYC, IntegrationProvider.KARZA): {
            "required_fields": ["api_key"],
            "optional_fields": ["api_secret", "redirect_url"],
            "description": "Karza Aadhaar verification configuration.",
            "documentation_url": None,
        },
        (IntegrationType.PAN_VERIFICATION, IntegrationProvider.NSDL_PAN): {
            "required_fields": ["client_id", "client_secret"],
            "optional_fields": ["purpose_code"],
            "description": "NSDL PAN verification configuration.",
            "documentation_url": None,
        },
        (IntegrationType.PAN_VERIFICATION, IntegrationProvider.PROTEAN): {
            "required_fields": ["client_id", "client_secret"],
            "optional_fields": ["purpose_code"],
            "description": "Protean PAN verification configuration.",
            "documentation_url": None,
        },
        (IntegrationType.PAN_VERIFICATION, IntegrationProvider.KARZA): {
            "required_fields": ["api_key"],
            "optional_fields": ["api_secret", "purpose_code"],
            "description": "Karza PAN verification configuration.",
            "documentation_url": None,
        },
        (IntegrationType.GSTN, IntegrationProvider.GSTN): {
            "required_fields": ["gstin", "username"],
            "optional_fields": ["password", "asp_id", "asp_secret", "auto_file_gstr1", "auto_file_gstr3b"],
            "description": "Direct GSTN portal integration for return filing",
            "documentation_url": "https://www.gst.gov.in/",
        },
        (IntegrationType.CREDIT_BUREAU, IntegrationProvider.CIBIL): {
            "required_fields": ["member_id", "member_password", "user_id"],
            "optional_fields": ["pfx_certificate", "pfx_password", "default_inquiry_type"],
            "description": "CIBIL credit bureau integration",
            "documentation_url": "https://www.cibil.com/",
        },
        (IntegrationType.CREDIT_BUREAU, IntegrationProvider.EXPERIAN): {
            "required_fields": ["member_id", "api_key", "api_secret"],
            "optional_fields": ["default_inquiry_type", "purpose_code"],
            "description": "Experian credit bureau integration",
            "documentation_url": "https://www.experian.in/",
        },
        (IntegrationType.PAYMENT_GATEWAY, IntegrationProvider.RAZORPAY): {
            "required_fields": ["key_id", "key_secret"],
            "optional_fields": ["webhook_secret", "payment_page_name", "theme_color", "logo_url"],
            "description": "Razorpay payment gateway for online collections",
            "documentation_url": "https://razorpay.com/docs/",
        },
        (IntegrationType.SMS_GATEWAY, IntegrationProvider.MSG91): {
            "required_fields": ["sender_id", "api_key", "dlt_entity_id"],
            "optional_fields": ["default_template_id", "auth_token"],
            "description": "MSG91 SMS gateway configuration with DLT metadata.",
            "documentation_url": "https://docs.msg91.com/",
        },
        (IntegrationType.EMAIL_GATEWAY, IntegrationProvider.SENDGRID): {
            "required_fields": ["from_email", "api_key"],
            "optional_fields": ["from_name", "webhook_secret"],
            "description": "SendGrid transactional email configuration.",
            "documentation_url": "https://docs.sendgrid.com/",
        },
        (IntegrationType.EMAIL_GATEWAY, IntegrationProvider.AWS_SES): {
            "required_fields": ["from_email", "api_key", "api_secret"],
            "optional_fields": ["from_name"],
            "description": "AWS SES transactional email configuration.",
            "documentation_url": "https://docs.aws.amazon.com/ses/",
        },
        (IntegrationType.E_INVOICE, IntegrationProvider.NIC_EINVOICE): {
            "required_fields": ["gstin", "username", "password"],
            "optional_fields": ["api_key", "api_secret"],
            "description": "NIC e-invoice and e-way bill API configuration.",
            "documentation_url": "https://einvoice1.gst.gov.in/",
        },
    }

    key = (integration_type, provider)
    template_data = templates.get(key, {
        "required_fields": ["api_key"],
        "optional_fields": [],
        "description": f"Configuration for {integration_type.value} with {provider.value}",
        "documentation_url": None,
    })

    return IntegrationConfigTemplate(
        integration_type=integration_type,
        provider=provider,
        **template_data,
    )
