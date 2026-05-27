"""Charge-registration workflow service — CERSAI / ROC / NeSL / DG-Shipping.

The plan calls for automated charge registration on sanction acceptance and
satisfaction on closure. Each per-vendor integration is a separate plugin
behind ``IntegrationConfig`` and a feature flag; this service is the
in-platform spine that:

- queues the registration as a lifecycle event (no external call yet),
- can be flipped to live mode per-tenant via ``IntegrationConfig``,
- emits the CHARGE_REGISTERED_* / CHARGE_SATISFIED_* events the timeline
  + reports depend on,
- is asset-class agnostic — picks the authority from ``mst_asset_class``
  (``registration_authority_code``).

Wire points:
- :func:`sanction_service.record_borrower_acceptance` enqueues an Arq job
  that calls :meth:`ChargeRegistrationService.register_for_loan`.
- :func:`foreclosure_service.process_foreclosure` /
  ``transfer_out_service.close`` call :meth:`satisfy_for_loan`.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.lending.lifecycle_event import LifecycleActorKind, LifecycleSubjectType
from app.models.lending.masters import AssetClass
from app.services.lending.lifecycle_service import LifecycleService

# Authority-code → lifecycle event verb for register / satisfy
_AUTHORITY_EVENTS: dict[str, tuple[str, str]] = {
    "CERSAI": ("CHARGE_REGISTERED_CERSAI", "CHARGE_SATISFIED_CERSAI"),
    "ROC": ("CHARGE_REGISTERED_ROC", "CHARGE_SATISFIED_ROC"),
    "NESL": ("CHARGE_REGISTERED_NESL", "CHARGE_SATISFIED_NESL"),
    "DG_SHIPPING": ("CHARGE_REGISTERED_DG_SHIPPING", "CHARGE_SATISFIED_DG_SHIPPING"),
    "MORTH": ("CHARGE_REGISTERED_MORTH", "CHARGE_SATISFIED_MORTH"),
    "NHAI": ("CHARGE_REGISTERED_NHAI", "CHARGE_SATISFIED_NHAI"),
}


class ChargeRegistrationService:
    """Register / satisfy security charges with the appropriate authority."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.lifecycle = LifecycleService(session)

    async def _resolve_authority(self, organization_id: UUID, asset_class_code: str | None) -> str:
        """Look up the registration authority from `mst_asset_class`.

        Falls back to CERSAI (the universal default for movable + immovable
        property in India) when the asset class doesn't pin a specific one.
        """
        if not asset_class_code:
            return "CERSAI"
        stmt = select(AssetClass).where(
            AssetClass.organization_id == organization_id,
            AssetClass.code == asset_class_code,
        )
        row = (await self.session.execute(stmt)).scalar_one_or_none()
        if row is None or not row.registration_authority_code:
            return "CERSAI"
        return row.registration_authority_code

    async def register_for_loan(
        self,
        *,
        organization_id: UUID,
        loan_account_id: UUID,
        actor_user_id: UUID | None,
        asset_class_code: str | None = None,
        registration_ref: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> str:
        """Emit a CHARGE_REGISTERED_* lifecycle event.

        Returns the authority code used. The actual external call to the
        registration portal is a separate plugin behind ``IntegrationConfig``
        — until that lights up, the lifecycle row is the audit-trail truth.
        """
        authority = await self._resolve_authority(organization_id, asset_class_code)
        register_verb, _ = _AUTHORITY_EVENTS.get(
            authority, (f"CHARGE_REGISTERED_{authority}", f"CHARGE_SATISFIED_{authority}")
        )
        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.LOAN_ACCOUNT,
            subject_id=loan_account_id,
            event_type=register_verb,
            actor_kind=(
                LifecycleActorKind.SYSTEM if actor_user_id is None else LifecycleActorKind.LENDER
            ),
            actor_user_id=actor_user_id,
            payload={
                "authority": authority,
                "registration_ref": registration_ref,
                **(payload or {}),
            },
            regulatory_tags=[register_verb],
        )
        return authority

    async def satisfy_for_loan(
        self,
        *,
        organization_id: UUID,
        loan_account_id: UUID,
        actor_user_id: UUID | None,
        asset_class_code: str | None = None,
        satisfaction_ref: str | None = None,
        reason: str | None = None,
    ) -> str:
        """Emit a CHARGE_SATISFIED_* lifecycle event at loan closure."""
        authority = await self._resolve_authority(organization_id, asset_class_code)
        _, satisfy_verb = _AUTHORITY_EVENTS.get(
            authority, (f"CHARGE_REGISTERED_{authority}", f"CHARGE_SATISFIED_{authority}")
        )
        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.LOAN_ACCOUNT,
            subject_id=loan_account_id,
            event_type=satisfy_verb,
            actor_kind=LifecycleActorKind.LENDER if actor_user_id else LifecycleActorKind.SYSTEM,
            actor_user_id=actor_user_id,
            payload={
                "authority": authority,
                "satisfaction_ref": satisfaction_ref,
                "reason": reason,
            },
            regulatory_tags=[satisfy_verb],
        )
        return authority
