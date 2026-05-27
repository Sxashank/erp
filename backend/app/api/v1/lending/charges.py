"""Charge-registration admin endpoints (CERSAI / ROC / NeSL / DG-Shipping).

Wraps :class:`ChargeRegistrationService` so operators can manually trigger or
re-fire a registration / satisfaction. Production call path: an Arq job on
sanction acceptance / loan closure invokes the same service directly.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.services.lending.charge_registration_service import ChargeRegistrationService

router = APIRouter(tags=["LMS - Charge Registration"])


@router.post("/loan-accounts/{loan_account_id}/charges/register")
async def register_charge(
    loan_account_id: UUID,
    payload: dict[str, Any] = Body(default_factory=dict),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
    _: None = Depends(RequirePermissions("LMS_CHARGE_REGISTER")),
) -> dict[str, Any]:
    """Trigger CERSAI / ROC / NeSL / DG-Shipping registration for a loan."""
    svc = ChargeRegistrationService(db)
    authority = await svc.register_for_loan(
        organization_id=user.organization_id,
        loan_account_id=loan_account_id,
        actor_user_id=user.id,
        asset_class_code=payload.get("asset_class_code"),
        registration_ref=payload.get("registration_ref"),
        payload=payload.get("payload"),
    )
    await db.commit()
    return {"loan_account_id": str(loan_account_id), "authority": authority, "status": "REGISTERED"}


@router.post("/loan-accounts/{loan_account_id}/charges/satisfy")
async def satisfy_charge(
    loan_account_id: UUID,
    payload: dict[str, Any] = Body(default_factory=dict),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
    _: None = Depends(RequirePermissions("LMS_CHARGE_SATISFY")),
) -> dict[str, Any]:
    """Mark a security charge satisfied at closure / transfer-out."""
    svc = ChargeRegistrationService(db)
    authority = await svc.satisfy_for_loan(
        organization_id=user.organization_id,
        loan_account_id=loan_account_id,
        actor_user_id=user.id,
        asset_class_code=payload.get("asset_class_code"),
        satisfaction_ref=payload.get("satisfaction_ref"),
        reason=payload.get("reason"),
    )
    await db.commit()
    return {"loan_account_id": str(loan_account_id), "authority": authority, "status": "SATISFIED"}
