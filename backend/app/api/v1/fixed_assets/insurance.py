"""Insurance API endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.auth.user import User
from app.core.constants import Permissions
from app.core.permissions import PermissionChecker
from app.models.fixed_assets.insurance import (
    InsurancePolicyStatus,
    InsuranceType,
    ClaimStatus,
)
from app.schemas.fixed_assets.insurance import (
    InsurancePolicyCreate,
    InsurancePolicyUpdate,
    InsurancePolicyRenew,
    InsurancePremiumPayment,
    InsurancePolicyResponse,
    InsuranceClaimCreate,
    InsuranceClaimUpdate,
    InsuranceClaimSettle,
    InsuranceClaimResponse,
    InsuranceSummaryResponse,
    InsuranceExpiryAlertResponse,
    PendingClaimsResponse,
)
from app.services.fixed_assets.insurance_service import InsuranceService

router = APIRouter()


def _policy_to_response(policy) -> InsurancePolicyResponse:
    """Convert policy model to response."""
    return InsurancePolicyResponse(
        id=policy.id,
        organization_id=policy.organization_id,
        policy_number=policy.policy_number,
        policy_name=policy.policy_name,
        insurance_type=policy.insurance_type,
        status=policy.status,
        insurer_name=policy.insurer_name,
        insurer_id=policy.insurer_id,
        broker_name=policy.broker_name,
        broker_id=policy.broker_id,
        contact_person=policy.contact_person,
        contact_phone=policy.contact_phone,
        contact_email=policy.contact_email,
        claim_helpline=policy.claim_helpline,
        start_date=policy.start_date,
        end_date=policy.end_date,
        days_until_expiry=policy.days_until_expiry,
        is_expiring_soon=policy.is_expiring_soon,
        sum_insured=policy.sum_insured,
        remaining_coverage=policy.remaining_coverage,
        coverage_description=policy.coverage_description,
        exclusions=policy.exclusions,
        deductible_amount=policy.deductible_amount,
        deductible_percentage=policy.deductible_percentage,
        base_premium=policy.base_premium,
        gst_rate=policy.gst_rate,
        gst_amount=policy.gst_amount,
        stamp_duty=policy.stamp_duty,
        total_premium=policy.total_premium,
        payment_mode=policy.payment_mode,
        next_premium_due=policy.next_premium_due,
        premium_paid=policy.premium_paid,
        premium_paid_date=policy.premium_paid_date,
        asset_ids=policy.asset_ids,
        asset_count=len(policy.asset_ids) if policy.asset_ids else 0,
        covers_all_assets=policy.covers_all_assets,
        total_claims_count=policy.total_claims_count,
        total_claims_amount=policy.total_claims_amount,
        total_settled_amount=policy.total_settled_amount,
        is_renewable=policy.is_renewable,
        renewal_reminder_days=policy.renewal_reminder_days,
        is_active=True,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
        created_by=policy.created_by,
        updated_by=policy.updated_by,
    )


def _claim_to_response(claim) -> InsuranceClaimResponse:
    """Convert claim model to response."""
    return InsuranceClaimResponse(
        id=claim.id,
        organization_id=claim.organization_id,
        policy_id=claim.policy_id,
        policy_number=claim.policy.policy_number if claim.policy else None,
        claim_number=claim.claim_number,
        insurer_claim_number=claim.insurer_claim_number,
        asset_id=claim.asset_id,
        asset_code=claim.asset.asset_code if claim.asset else None,
        asset_name=claim.asset.asset_name if claim.asset else None,
        status=claim.status,
        incident_date=claim.incident_date,
        incident_description=claim.incident_description,
        incident_location=claim.incident_location,
        cause_of_loss=claim.cause_of_loss,
        reported_date=claim.reported_date,
        reported_by=claim.reported_by,
        fir_number=claim.fir_number,
        fir_date=claim.fir_date,
        estimated_loss=claim.estimated_loss,
        claim_amount=claim.claim_amount,
        deductible_applied=claim.deductible_applied,
        approved_amount=claim.approved_amount,
        settled_amount=claim.settled_amount,
        rejection_reason=claim.rejection_reason,
        submitted_date=claim.submitted_date,
        surveyor_assigned_date=claim.surveyor_assigned_date,
        surveyor_name=claim.surveyor_name,
        surveyor_report_date=claim.surveyor_report_date,
        approval_date=claim.approval_date,
        settlement_date=claim.settlement_date,
        payment_received_date=claim.payment_received_date,
        payment_reference=claim.payment_reference,
        processing_days=claim.processing_days,
        asset_written_off=claim.asset_written_off,
        asset_repaired=claim.asset_repaired,
        repair_cost=claim.repair_cost,
        is_active=True,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
        created_by=claim.created_by,
        updated_by=claim.updated_by,
    )


# ============================================
# Policy Endpoints
# ============================================

@router.get("/policies", response_model=dict)
async def list_policies(
    request: Request,
    organization_id: UUID,
    status: Optional[InsurancePolicyStatus] = None,
    insurance_type: Optional[InsuranceType] = None,
    expiring_within_days: Optional[int] = Query(None, ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """List insurance policies."""
    service = InsuranceService(db)
    policies, total = await service.list_policies(
        organization_id, status, insurance_type, expiring_within_days, skip, limit
    )

    return {
        "items": [_policy_to_response(p) for p in policies],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/policies/{policy_id}", response_model=InsurancePolicyResponse)
async def get_policy(
    request: Request,
    policy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get insurance policy by ID."""
    service = InsuranceService(db)
    policy = await service.get_policy(policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )
    return _policy_to_response(policy)


@router.post("/policies", response_model=InsurancePolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    request: Request,
    data: InsurancePolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_CREATE])),
):
    """Create a new insurance policy."""
    service = InsuranceService(db)
    try:
        policy = await service.create_policy(data, created_by=current_user.id)
        return _policy_to_response(policy)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/policies/{policy_id}", response_model=InsurancePolicyResponse)
async def update_policy(
    request: Request,
    policy_id: UUID,
    data: InsurancePolicyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Update insurance policy."""
    service = InsuranceService(db)
    policy = await service.update_policy(policy_id, data, updated_by=current_user.id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )
    return _policy_to_response(policy)


@router.post("/policies/{policy_id}/activate", response_model=InsurancePolicyResponse)
async def activate_policy(
    request: Request,
    policy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Activate an insurance policy."""
    service = InsuranceService(db)
    try:
        policy = await service.activate_policy(policy_id, activated_by=current_user.id)
        return _policy_to_response(policy)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/policies/{policy_id}/pay-premium", response_model=InsurancePolicyResponse)
async def record_premium_payment(
    request: Request,
    policy_id: UUID,
    data: InsurancePremiumPayment,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Record premium payment for a policy."""
    service = InsuranceService(db)
    try:
        policy = await service.record_premium_payment(
            policy_id, data, recorded_by=current_user.id
        )
        return _policy_to_response(policy)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/policies/{policy_id}/renew", response_model=InsurancePolicyResponse)
async def renew_policy(
    request: Request,
    policy_id: UUID,
    data: InsurancePolicyRenew,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_CREATE])),
):
    """Renew an insurance policy."""
    service = InsuranceService(db)
    try:
        policy = await service.renew_policy(policy_id, data, renewed_by=current_user.id)
        return _policy_to_response(policy)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================
# Claim Endpoints
# ============================================

@router.get("/claims", response_model=dict)
async def list_claims(
    request: Request,
    organization_id: UUID,
    policy_id: Optional[UUID] = None,
    asset_id: Optional[UUID] = None,
    status: Optional[ClaimStatus] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """List insurance claims."""
    service = InsuranceService(db)
    claims, total = await service.list_claims(
        organization_id, policy_id, asset_id, status, from_date, to_date, skip, limit
    )

    return {
        "items": [_claim_to_response(c) for c in claims],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/claims/{claim_id}", response_model=InsuranceClaimResponse)
async def get_claim(
    request: Request,
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get insurance claim by ID."""
    service = InsuranceService(db)
    claim = await service.get_claim(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )
    return _claim_to_response(claim)


@router.post("/claims", response_model=InsuranceClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_claim(
    request: Request,
    data: InsuranceClaimCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_CREATE])),
):
    """Create a new insurance claim."""
    service = InsuranceService(db)
    try:
        claim = await service.create_claim(data, created_by=current_user.id)
        return _claim_to_response(claim)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/claims/{claim_id}", response_model=InsuranceClaimResponse)
async def update_claim(
    request: Request,
    claim_id: UUID,
    data: InsuranceClaimUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Update insurance claim."""
    service = InsuranceService(db)
    claim = await service.update_claim(claim_id, data, updated_by=current_user.id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )
    return _claim_to_response(claim)


@router.post("/claims/{claim_id}/submit", response_model=InsuranceClaimResponse)
async def submit_claim(
    request: Request,
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Submit a claim to insurer."""
    service = InsuranceService(db)
    try:
        claim = await service.submit_claim(claim_id, submitted_by=current_user.id)
        return _claim_to_response(claim)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/claims/{claim_id}/settle", response_model=InsuranceClaimResponse)
async def settle_claim(
    request: Request,
    claim_id: UUID,
    data: InsuranceClaimSettle,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Settle an insurance claim."""
    service = InsuranceService(db)
    try:
        claim = await service.settle_claim(claim_id, data, settled_by=current_user.id)
        return _claim_to_response(claim)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================
# Analytics Endpoints
# ============================================

@router.get("/summary", response_model=InsuranceSummaryResponse)
async def get_insurance_summary(
    request: Request,
    organization_id: UUID,
    as_on_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_REPORT_VIEW])),
):
    """Get insurance portfolio summary."""
    service = InsuranceService(db)
    return await service.get_insurance_summary(organization_id, as_on_date)


@router.get("/alerts/expiry", response_model=InsuranceExpiryAlertResponse)
async def get_policy_expiry_alerts(
    request: Request,
    organization_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get policies expiring within specified days."""
    service = InsuranceService(db)
    policies = await service.get_expiring_policies(organization_id, days)

    total_sum = sum(p.sum_insured for p in policies)

    return InsuranceExpiryAlertResponse(
        policies_expiring=[_policy_to_response(p) for p in policies],
        total_count=len(policies),
        total_sum_insured_at_risk=total_sum,
    )


@router.get("/alerts/pending-claims", response_model=PendingClaimsResponse)
async def get_pending_claims_alert(
    request: Request,
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get all pending insurance claims."""
    service = InsuranceService(db)
    claims = await service.get_pending_claims(organization_id)

    total_amount = sum(c.claim_amount for c in claims)
    oldest_days = max((c.processing_days for c in claims), default=0)

    return PendingClaimsResponse(
        claims=[_claim_to_response(c) for c in claims],
        total_count=len(claims),
        total_claim_amount=total_amount,
        oldest_claim_days=oldest_days,
    )
