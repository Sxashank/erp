"""Disposal register and approval helpers for fixed-assets operational core."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import ApprovalRequestStatus, AssetDisposalType, AssetStatus
from app.models.approval.approval import ApprovalRequest
from app.models.fixed_assets.fixed_asset import FixedAsset
from app.schemas.fixed_assets.disposal import DisposalRegisterItem


DISPOSAL_REQUEST_ENTITY_TYPE = "FixedAssetDisposal"


class DisposalService:
    """Service for disposal register queries and approval finalization."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_register(
        self,
        organization_id: UUID,
        status: Optional[str] = None,
        disposal_type: Optional[AssetDisposalType] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[list[DisposalRegisterItem], int]:
        """List disposal register rows from assets plus approval requests."""
        disposed_assets = await self._get_disposed_assets(
            organization_id=organization_id,
            disposal_type=disposal_type,
            search=search,
        )
        pending_requests = await self._get_disposal_requests(
            organization_id=organization_id,
            status=status,
            search=search,
        )

        items = [
            self._item_from_asset(asset)
            for asset in disposed_assets
            if self._matches_status_filter("COMPLETED", status)
        ]
        items.extend(self._item_from_request(request) for request in pending_requests)

        items.sort(
            key=lambda item: (
                item.request_date
                or (
                    datetime.combine(item.disposal_date, datetime.min.time(), tzinfo=timezone.utc)
                    if item.disposal_date
                    else datetime.min.replace(tzinfo=timezone.utc)
                )
            ),
            reverse=True,
        )

        total = len(items)
        return items[skip : skip + limit], total

    async def get_register_item(
        self,
        asset_id: UUID,
    ) -> Optional[DisposalRegisterItem]:
        """Get disposal register row for an asset, including pending request state."""
        request = await self._get_request_by_asset_id(asset_id)
        if request:
            return self._item_from_request(request)

        asset = await self._get_asset(asset_id)
        if not asset or asset.status != AssetStatus.DISPOSED:
            return None
        return self._item_from_asset(asset)

    async def finalize_approved_request(
        self,
        request: ApprovalRequest,
        approved_by: UUID,
    ) -> FixedAsset:
        """Execute the domain mutation for an approved disposal request."""
        from app.schemas.fixed_assets.fixed_asset import AssetDisposeRequest
        from app.services.fixed_assets.asset_service import AssetService

        payload = (request.request_details or {}).get("payload") or {}
        disposal_payload = payload.get("disposal") or {}
        dispose_request = AssetDisposeRequest.model_validate(disposal_payload)

        service = AssetService(self.session)
        return await service.dispose(
            request.entity_id,
            dispose_request,
            disposed_by=approved_by,
        )

    async def _get_disposed_assets(
        self,
        organization_id: UUID,
        disposal_type: Optional[AssetDisposalType],
        search: Optional[str],
    ) -> Sequence[FixedAsset]:
        query = (
            select(FixedAsset)
            .options(
                selectinload(FixedAsset.category),
                selectinload(FixedAsset.vendor),
            )
            .where(
                FixedAsset.organization_id == organization_id,
                FixedAsset.is_active == True,
                FixedAsset.status == AssetStatus.DISPOSED,
            )
        )
        if disposal_type:
            query = query.where(FixedAsset.disposal_type == disposal_type)
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    FixedAsset.asset_code.ilike(term),
                    FixedAsset.asset_name.ilike(term),
                )
            )
        result = await self.session.execute(query.order_by(FixedAsset.disposal_date.desc(), FixedAsset.updated_at.desc()))
        return result.scalars().all()

    async def _get_disposal_requests(
        self,
        organization_id: UUID,
        status: Optional[str],
        search: Optional[str],
    ) -> Sequence[ApprovalRequest]:
        request_statuses = [
            ApprovalRequestStatus.PENDING,
            ApprovalRequestStatus.REJECTED,
            ApprovalRequestStatus.RETURNED,
            ApprovalRequestStatus.CANCELLED,
        ]
        if status:
            request_statuses = [
                request_status
                for request_status in request_statuses
                if request_status.value == status
            ]
        if not request_statuses:
            return []

        query = (
            select(ApprovalRequest)
            .options(selectinload(ApprovalRequest.requester))
            .where(
                ApprovalRequest.organization_id == organization_id,
                ApprovalRequest.entity_type == DISPOSAL_REQUEST_ENTITY_TYPE,
                ApprovalRequest.status.in_(request_statuses),
            )
        )
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    ApprovalRequest.request_summary.ilike(term),
                    ApprovalRequest.request_number.ilike(term),
                )
            )
        result = await self.session.execute(query.order_by(ApprovalRequest.requested_at.desc()))
        return result.scalars().all()

    async def _get_request_by_asset_id(self, asset_id: UUID) -> Optional[ApprovalRequest]:
        query = (
            select(ApprovalRequest)
            .options(selectinload(ApprovalRequest.requester))
            .where(
                ApprovalRequest.entity_type == DISPOSAL_REQUEST_ENTITY_TYPE,
                ApprovalRequest.entity_id == asset_id,
                ApprovalRequest.status.in_(
                    [
                        ApprovalRequestStatus.PENDING,
                        ApprovalRequestStatus.REJECTED,
                        ApprovalRequestStatus.RETURNED,
                        ApprovalRequestStatus.CANCELLED,
                    ]
                ),
            )
            .order_by(ApprovalRequest.requested_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def _get_asset(self, asset_id: UUID) -> Optional[FixedAsset]:
        query = (
            select(FixedAsset)
            .options(selectinload(FixedAsset.category), selectinload(FixedAsset.vendor))
            .where(FixedAsset.id == asset_id, FixedAsset.is_active == True)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    def _item_from_asset(self, asset: FixedAsset) -> DisposalRegisterItem:
        return DisposalRegisterItem(
            asset_id=asset.id,
            organization_id=asset.organization_id,
            asset_code=asset.asset_code,
            asset_name=asset.asset_name,
            category_id=asset.category_id,
            category_name=asset.category.category_name if asset.category else None,
            disposal_type=asset.disposal_type,
            disposal_date=asset.disposal_date,
            request_date=asset.updated_at,
            requested_by=asset.updated_by,
            original_cost=asset.total_cost,
            accumulated_depreciation=asset.accumulated_depreciation,
            book_value=asset.total_cost - asset.accumulated_depreciation,
            disposal_value=asset.disposal_value,
            disposal_gain_loss=asset.disposal_gain_loss,
            remarks=asset.disposal_remarks,
            status="COMPLETED",
            source="DISPOSED_ASSET",
        )

    def _item_from_request(self, request: ApprovalRequest) -> DisposalRegisterItem:
        payload = (request.request_details or {}).get("payload") or {}
        disposal_payload = payload.get("disposal") or {}
        return DisposalRegisterItem(
            asset_id=request.entity_id,
            organization_id=request.organization_id,
            asset_code=payload.get("asset_code", "Unknown"),
            asset_name=payload.get("asset_name", "Unknown"),
            category_id=UUID(payload["category_id"]) if payload.get("category_id") else UUID(int=0),
            category_name=payload.get("category_name"),
            disposal_type=disposal_payload.get("disposal_type"),
            disposal_date=disposal_payload.get("disposal_date"),
            request_date=request.requested_at,
            requested_by=request.requested_by,
            requested_by_name=request.requester.full_name if request.requester else None,
            approval_request_id=request.id,
            approval_request_number=request.request_number,
            approval_status=request.status,
            original_cost=payload.get("original_cost", "0.00"),
            accumulated_depreciation=payload.get("accumulated_depreciation", "0.00"),
            book_value=payload.get("book_value", "0.00"),
            disposal_value=disposal_payload.get("disposal_value"),
            remarks=disposal_payload.get("disposal_remarks"),
            buyer_name=disposal_payload.get("buyer_name"),
            status=self._map_request_status(request.status),
            source="APPROVAL_REQUEST",
        )

    def _map_request_status(self, status: ApprovalRequestStatus) -> str:
        mapping = {
            ApprovalRequestStatus.PENDING: "PENDING_APPROVAL",
            ApprovalRequestStatus.REJECTED: "REJECTED",
            ApprovalRequestStatus.RETURNED: "RETURNED",
            ApprovalRequestStatus.CANCELLED: "CANCELLED",
        }
        return mapping.get(status, status.value)

    def _matches_status_filter(self, row_status: str, filter_status: Optional[str]) -> bool:
        return not filter_status or row_status == filter_status
