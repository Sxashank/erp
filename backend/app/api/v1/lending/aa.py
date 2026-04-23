"""Account Aggregator API endpoints for consent management and data fetching."""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, RequirePermissions
from app.models.auth.user import User
from app.models.lending.enums import (
    AAProvider, AAConsentStatus, AAFIType, AAFetchSessionStatus
)
from app.services.lending.aa_service import AAService
from app.schemas.lending.aa import (
    AAConsentRequestInitiate,
    AAConsentInitiateResponse,
    AAConsentResponse,
    AAConsentDetailResponse,
    AAConsentListResponse,
    AAConsentRevokeRequest,
    AAFetchDataRequest,
    AAFetchDataResponse,
    AAFetchSessionResponse,
    AAFetchSessionDetailResponse,
    AAFetchSessionListResponse,
    AABankAccountResponse,
    AABankAccountDetailResponse,
    AABankAccountListResponse,
    AABankTransactionListResponse,
    AAConsentStatistics,
    AAFetchStatistics,
    AAConsentLogListResponse,
    AAConsentLogResponse,
)

router = APIRouter(prefix="/aa", tags=["Account Aggregator"])


# =============================================================================
# Consent Endpoints
# =============================================================================


@router.post(
    "/consents",
    response_model=AAConsentInitiateResponse,
    summary="Initiate consent request",
    description="Create a new consent request with AA provider. Returns URL for customer approval.",
)
async def initiate_consent(
    request: AAConsentRequestInitiate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("aa.consent.create")),
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/consents",
    response_model=AAConsentListResponse,
    summary="List consents",
    description="List all AA consents for the organization with filtering options.",
)
async def list_consents(
    organization_id: UUID,
    entity_id: Optional[UUID] = None,
    status: Optional[AAConsentStatus] = None,
    provider: Optional[AAProvider] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("aa.consent.read")),
):
    """List AA consents with filtering."""
    service = AAService(db)
    return await service.list_consents(
        organization_id=organization_id,
        entity_id=entity_id,
        status=status,
        provider=provider,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/consents/{consent_id}",
    response_model=AAConsentDetailResponse,
    summary="Get consent details",
    description="Get detailed information about a specific consent including fetch sessions.",
)
async def get_consent(
    consent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("aa.consent.read")),
):
    """Get consent details by ID."""
    service = AAService(db)
    try:
        return await service.get_consent(consent_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/consents/{consent_id}/check-status",
    response_model=AAConsentResponse,
    summary="Check consent status",
    description="Check and sync consent status with AA provider.",
)
async def check_consent_status(
    consent_id: UUID,
    sync_with_provider: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("aa.consent.read")),
):
    """Check and update consent status from AA provider."""
    service = AAService(db)
    try:
        return await service.check_consent_status(
            consent_id=consent_id,
            sync_with_provider=sync_with_provider,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/consents/{consent_id}/revoke",
    response_model=AAConsentResponse,
    summary="Revoke consent",
    description="Revoke an active consent. This will notify the AA provider.",
)
async def revoke_consent(
    consent_id: UUID,
    request: AAConsentRevokeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("aa.consent.revoke")),
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# Data Fetch Endpoints
# =============================================================================


@router.post(
    "/consents/{consent_id}/fetch",
    response_model=AAFetchDataResponse,
    summary="Initiate data fetch",
    description="Start fetching financial data for an approved consent.",
)
async def initiate_data_fetch(
    consent_id: UUID,
    request: AAFetchDataRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("aa.data.fetch")),
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/consents/{consent_id}/sessions",
    response_model=AAFetchSessionListResponse,
    summary="List fetch sessions",
    description="List all data fetch sessions for a consent.",
)
async def list_fetch_sessions(
    consent_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("aa.data.read")),
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
    summary="Get session details",
    description="Get detailed information about a fetch session including accounts.",
)
async def get_fetch_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("aa.data.read")),
):
    """Get fetch session details by ID."""
    service = AAService(db)
    try:
        return await service.get_fetch_session(session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/sessions/{session_id}/fetch-data",
    response_model=AAFetchSessionDetailResponse,
    summary="Fetch session data",
    description="Pull actual financial data for a fetch session. Call after FI notification.",
)
async def fetch_session_data(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("aa.data.fetch")),
):
    """Fetch and process data for a session.

    This should be called after receiving FI notification from webhook
    or to poll for data after initiation.
    """
    service = AAService(db)
    try:
        return await service.fetch_session_data(session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# Bank Account Endpoints
# =============================================================================


@router.get(
    "/bank-accounts",
    response_model=AABankAccountListResponse,
    summary="List bank accounts",
    description="List all fetched bank accounts for the organization.",
)
async def list_bank_accounts(
    organization_id: UUID,
    entity_id: Optional[UUID] = None,
    fi_type: Optional[AAFIType] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("aa.data.read")),
):
    """List fetched bank accounts."""
    service = AAService(db)
    return await service.list_bank_accounts(
        organization_id=organization_id,
        entity_id=entity_id,
        fi_type=fi_type,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/bank-accounts/{account_id}",
    response_model=AABankAccountDetailResponse,
    summary="Get bank account details",
    description="Get detailed information about a fetched bank account including transactions.",
)
async def get_bank_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("aa.data.read")),
):
    """Get bank account details by ID."""
    service = AAService(db)
    try:
        return await service.get_bank_account(account_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/bank-accounts/{account_id}/transactions",
    response_model=AABankTransactionListResponse,
    summary="List account transactions",
    description="List transactions for a specific bank account.",
)
async def list_account_transactions(
    account_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    txn_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("aa.data.read")),
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
    summary="Get consent statistics",
    description="Get aggregated statistics about AA consents.",
)
async def get_consent_statistics(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("aa.statistics.read")),
):
    """Get consent statistics for organization."""
    service = AAService(db)
    return await service.get_consent_statistics(organization_id)


@router.get(
    "/statistics/fetches",
    response_model=AAFetchStatistics,
    summary="Get fetch statistics",
    description="Get aggregated statistics about data fetches.",
)
async def get_fetch_statistics(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("aa.statistics.read")),
):
    """Get fetch statistics for organization."""
    service = AAService(db)
    return await service.get_fetch_statistics(organization_id)


# =============================================================================
# Provider Configuration Endpoints
# =============================================================================


@router.get(
    "/providers",
    summary="List supported providers",
    description="Get list of supported AA providers.",
)
async def list_providers(
    current_user: User = Depends(RequirePermissions("aa.consent.read")),
):
    """List supported AA providers."""
    from app.integrations.aa.factory import AAClientFactory

    providers = AAClientFactory.get_supported_providers()
    return {
        "providers": providers,
        "schemas": {
            p: AAClientFactory.get_provider_config_schema(p)
            for p in providers
        }
    }
