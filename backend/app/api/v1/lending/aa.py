"""Account Aggregator API endpoints for consent management and data fetching."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.models.lending.enums import AAConsentStatus, AAFIType, AAProvider
from app.schemas.base import PaginatedResponse as PaginatedResponseBase
from app.schemas.lending.aa import (
    AABankAccountDetailResponse,
    AABankAccountListResponse,
    AABankTransactionListResponse,
    AAConsentDetailResponse,
    AAConsentInitiateResponse,
    AAConsentListItemResponse,
    AAConsentRequestInitiate,
    AAConsentResponse,
    AAConsentRevokeRequest,
    AAConsentStatistics,
    AAFetchDataRequest,
    AAFetchDataResponse,
    AAFetchSessionDetailResponse,
    AAFetchSessionListResponse,
    AAFetchStatistics,
)
from app.services.lending.aa_service import AAService
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter(prefix="/aa", tags=["Account Aggregator"])


# =============================================================================
# Consent Endpoints
# =============================================================================


@router.post(
    "/consents",
    response_model=AAConsentInitiateResponse,
    response_model_by_alias=True,
    summary="Initiate consent request",
    description="Create a new consent request with AA provider. Returns URL for customer approval.",
)
async def initiate_consent(
    request: AAConsentRequestInitiate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("AA_CONSENT_CREATE")),
):
    """Initiate a new AA consent request.

    The customer will need to approve this consent via their AA app.
    The consent URL returned should be shared with the customer.
    """
    service = AAService(db)
    try:
        return await service.initiate_consent(
            request=request,
            created_by_id=current_user.id,
        )
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get(
    "/consents",
    response_model=PaginatedResponseBase[AAConsentListItemResponse],
    response_model_by_alias=True,
    summary="List consents",
    description="List all AA consents for the caller's organization with filtering options.",
)
async def list_consents(
    entity_id: UUID | None = None,
    status: AAConsentStatus | None = None,
    provider: AAProvider | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("AA_CONSENT_READ")),
):
    """List AA consents (camelCase, scoped to caller's org)."""
    service = AAService(db)
    items, total = await service.list_consents_for_org(
        organization_id=current_user.organization_id,
        entity_id=entity_id,
        status=status,
        provider=provider,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    list_items = [AAConsentListItemResponse.model_validate(c) for c in items]
    return PaginatedResponseBase.create(list_items, total, page, page_size)


@router.get(
    "/consents/{consent_id}",
    response_model=AAConsentDetailResponse,
    response_model_by_alias=True,
    summary="Get consent details",
    description="Get detailed information about a specific consent including fetch sessions.",
)
async def get_consent(
    consent_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("AA_CONSENT_READ")),
):
    """Get consent details by ID."""
    service = AAService(db)
    try:
        return await service.get_consent(consent_id)
    except ValueError as e:
        raise NotFoundException(detail=str(e), error_code="NOT_FOUND")


@router.post(
    "/consents/{consent_id}/check-status",
    response_model=AAConsentResponse,
    response_model_by_alias=True,
    summary="Check consent status",
    description="Check and sync consent status with AA provider.",
)
async def check_consent_status(
    consent_id: UUID,
    sync_with_provider: bool = True,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("AA_CONSENT_READ")),
):
    """Check and update consent status from AA provider."""
    service = AAService(db)
    try:
        return await service.check_consent_status(
            consent_id=consent_id,
            sync_with_provider=sync_with_provider,
        )
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/consents/{consent_id}/revoke",
    response_model=AAConsentResponse,
    response_model_by_alias=True,
    summary="Revoke consent",
    description="Revoke an active consent. This will notify the AA provider.",
)
async def revoke_consent(
    consent_id: UUID,
    request: AAConsentRevokeRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("AA_CONSENT_REVOKE")),
):
    """Revoke an active AA consent."""
    service = AAService(db)
    try:
        return await service.revoke_consent(
            consent_id=consent_id,
            reason=request.reason,
            revoked_by_id=current_user.id,
        )
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# =============================================================================
# Data Fetch Endpoints
# =============================================================================


@router.post(
    "/consents/{consent_id}/fetch",
    response_model=AAFetchDataResponse,
    response_model_by_alias=True,
    summary="Initiate data fetch",
    description="Start fetching financial data for an approved consent.",
)
async def initiate_data_fetch(
    consent_id: UUID,
    request: AAFetchDataRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("AA_DATA_FETCH")),
):
    """Initiate FI data fetch for an approved consent.

    The consent must be in ACTIVE or APPROVED status.
    Data will be fetched asynchronously from FIPs.
    """
    # Ensure consent_id matches
    request.consent_id = consent_id
    service = AAService(db)
    try:
        return await service.initiate_data_fetch(request=request)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get(
    "/consents/{consent_id}/sessions",
    response_model=AAFetchSessionListResponse,
    response_model_by_alias=True,
    summary="List fetch sessions",
    description="List all data fetch sessions for a consent.",
)
async def list_fetch_sessions(
    consent_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("AA_DATA_READ")),
):
    """List fetch sessions for a consent."""
    service = AAService(db)
    return await service.list_fetch_sessions(
        consent_id=consent_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/sessions/{session_id}",
    response_model=AAFetchSessionDetailResponse,
    response_model_by_alias=True,
    summary="Get session details",
    description="Get detailed information about a fetch session including accounts.",
)
async def get_fetch_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("AA_DATA_READ")),
):
    """Get fetch session details by ID."""
    service = AAService(db)
    try:
        return await service.get_fetch_session(session_id)
    except ValueError as e:
        raise NotFoundException(detail=str(e), error_code="NOT_FOUND")


@router.post(
    "/sessions/{session_id}/fetch-data",
    response_model=AAFetchSessionDetailResponse,
    response_model_by_alias=True,
    summary="Fetch session data",
    description="Pull actual financial data for a fetch session. Call after FI notification.",
)
async def fetch_session_data(
    session_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("AA_DATA_FETCH")),
):
    """Fetch and process data for a session.

    This should be called after receiving FI notification from webhook
    or to poll for data after initiation.
    """
    service = AAService(db)
    try:
        return await service.fetch_session_data(session_id)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# =============================================================================
# Bank Account Endpoints
# =============================================================================


@router.get(
    "/bank-accounts",
    response_model=AABankAccountListResponse,
    response_model_by_alias=True,
    summary="List bank accounts",
    description="List all fetched bank accounts for the organization.",
)
async def list_bank_accounts(
    entity_id: UUID | None = None,
    fi_type: AAFIType | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("AA_DATA_READ")),
):
    """List fetched bank accounts."""
    service = AAService(db)
    return await service.list_bank_accounts(
        organization_id=current_user.organization_id,
        entity_id=entity_id,
        fi_type=fi_type,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/bank-accounts/{account_id}",
    response_model=AABankAccountDetailResponse,
    response_model_by_alias=True,
    summary="Get bank account details",
    description="Get detailed information about a fetched bank account including transactions.",
)
async def get_bank_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("AA_DATA_READ")),
):
    """Get bank account details by ID."""
    service = AAService(db)
    try:
        return await service.get_bank_account(account_id)
    except ValueError as e:
        raise NotFoundException(detail=str(e), error_code="NOT_FOUND")


@router.get(
    "/bank-accounts/{account_id}/transactions",
    response_model=AABankTransactionListResponse,
    response_model_by_alias=True,
    summary="List account transactions",
    description="List transactions for a specific bank account.",
)
async def list_account_transactions(
    account_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    txn_type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("AA_DATA_READ")),
):
    """List transactions for a bank account."""
    service = AAService(db)
    return await service.list_transactions(
        bank_account_id=account_id,
        start_date=start_date,
        end_date=end_date,
        txn_type=txn_type,
        page=page,
        page_size=page_size,
    )


# =============================================================================
# Statistics Endpoints
# =============================================================================


@router.get(
    "/statistics/consents",
    response_model=AAConsentStatistics,
    response_model_by_alias=True,
    summary="Get consent statistics",
    description="Get aggregated statistics about AA consents.",
)
async def get_consent_statistics(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("AA_STATISTICS_READ")),
):
    """Get consent statistics for organization."""
    service = AAService(db)
    return await service.get_consent_statistics(current_user.organization_id)


@router.get(
    "/statistics/fetches",
    response_model=AAFetchStatistics,
    response_model_by_alias=True,
    summary="Get fetch statistics",
    description="Get aggregated statistics about data fetches.",
)
async def get_fetch_statistics(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("AA_STATISTICS_READ")),
):
    """Get fetch statistics for organization."""
    service = AAService(db)
    return await service.get_fetch_statistics(current_user.organization_id)


# =============================================================================
# Provider Configuration Endpoints
# =============================================================================


@router.get(
    "/providers",
    summary="List supported providers",
    description="Get list of supported AA providers.",
)
async def list_providers(
    current_user: User = Depends(RequirePermissions("AA_CONSENT_READ")),
):
    """List supported AA providers."""
    from app.integrations.aa.factory import AAClientFactory

    providers = AAClientFactory.get_supported_providers()
    return {
        "providers": providers,
        "schemas": {p: AAClientFactory.get_provider_config_schema(p) for p in providers},
    }
