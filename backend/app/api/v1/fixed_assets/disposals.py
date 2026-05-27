"""Disposal register API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_with_tenant
from app.core.constants import ApprovalWorkflowType, AssetDisposalType, Permissions
from app.core.permissions import PermissionChecker
from app.models.auth.user import User
from app.schemas.approval.approval import ApprovalRequestCreate
from app.schemas.fixed_assets.disposal import (
    DisposalRegisterActionResponse,
    DisposalRegisterItem,
    DisposalRegisterListResponse,
)
from app.schemas.fixed_assets.fixed_asset import AssetDisposeRequest
from app.services.approval.approval_service import ApprovalService
from app.services.fixed_assets.asset_service import AssetService
from app.services.fixed_assets.disposal_service import (
    DISPOSAL_REQUEST_ENTITY_TYPE,
    DisposalService,
)
from app.core.exceptions import ConflictException, NotFoundException

router = APIRouter()


@router.get("", response_model=DisposalRegisterListResponse, response_model_by_alias=True)
async def list_disposals(
    request: Request,
    status: str | None = Query(None),
    disposal_type: AssetDisposalType | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """List disposal register rows."""
    service = DisposalService(db)
    items, total = await service.list_register(
        organization_id=current_user.organization_id,
        status=status,
        disposal_type=disposal_type,
        search=search,
        skip=skip,
        limit=limit,
    )
    return DisposalRegisterListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{asset_id}", response_model=DisposalRegisterItem, response_model_by_alias=True)
async def get_disposal(
    request: Request,
    asset_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get disposal register row for one asset."""
    service = DisposalService(db)
    item = await service.get_register_item(asset_id)
    if not item:
        raise NotFoundException(
            detail="Disposal record not found",
            error_code="DISPOSAL_RECORD_NOT_FOUND",
        )
    return item


@router.post(
    "/{asset_id}/submit",
    response_model=DisposalRegisterActionResponse,
    response_model_by_alias=True,
)
async def submit_disposal(
    request: Request,
    asset_id: UUID,
    data: AssetDisposeRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_DISPOSE])),
):
    """Submit disposal for approval, or dispose immediately if approval is not required."""
    asset_service = AssetService(db)
    asset = await asset_service.get(asset_id)
    if not asset:
        raise NotFoundException(detail="Asset not found", error_code="ASSET_NOT_FOUND")

    approval_service = ApprovalService(db)
    approval_check = await approval_service.check_approval_required(
        organization_id=asset.organization_id,
        workflow_type=ApprovalWorkflowType.FA_ASSET_DISPOSAL,
        amount=asset.wdv_value,
    )

    disposal_service = DisposalService(db)
    if not approval_check.requires_approval:
        await asset_service.dispose(asset_id, data, disposed_by=current_user.id)
        item = await disposal_service.get_register_item(asset_id)
        return DisposalRegisterActionResponse(
            mode="disposed",
            message="Asset disposed successfully",
            disposal=item,
        )

    existing = await approval_service.get_request_by_entity(
        DISPOSAL_REQUEST_ENTITY_TYPE,
        asset_id,
    )
    if existing:
        raise ConflictException(
            detail=f"Disposal request already pending: {existing.request_number}",
            error_code="DISPOSAL_REQUEST_ALREADY_PENDING",
        )

    approval_request = await approval_service.submit_for_approval(
        ApprovalRequestCreate(
            organization_id=asset.organization_id,
            workflow_type=ApprovalWorkflowType.FA_ASSET_DISPOSAL,
            entity_type=DISPOSAL_REQUEST_ENTITY_TYPE,
            entity_id=asset_id,
            request_amount=asset.wdv_value,
            request_summary=f"Dispose asset {asset.asset_code} - {asset.asset_name}",
            request_details={
                "execution_target": "fixed_assets_disposal",
                "payload": {
                    "asset_code": asset.asset_code,
                    "asset_name": asset.asset_name,
                    "category_id": str(asset.category_id),
                    "category_name": asset.category.category_name if asset.category else None,
                    "original_cost": str(asset.total_cost),
                    "accumulated_depreciation": str(asset.accumulated_depreciation),
                    "book_value": str(asset.wdv_value),
                    "disposal": data.model_dump(mode="json"),
                },
            },
        ),
        requested_by=current_user.id,
    )
    await db.commit()
    item = await disposal_service.get_register_item(asset_id)
    return DisposalRegisterActionResponse(
        mode="submitted_for_approval",
        message="Disposal submitted for approval",
        disposal=item,
        approval_request_id=approval_request.id,
        approval_request_number=approval_request.request_number,
        approval_status=approval_request.status,
    )
