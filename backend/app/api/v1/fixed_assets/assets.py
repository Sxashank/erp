"""Fixed Asset API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.auth.user import User
from app.core.constants import AssetStatus, Permissions
from app.core.permissions import PermissionChecker
from app.schemas.fixed_assets.fixed_asset import (
    FixedAssetCreate,
    FixedAssetUpdate,
    FixedAssetResponse,
    AssetCapitalizeRequest,
    AssetDisposeRequest,
    AssetTransferRequest,
    AssetRevalueRequest,
    AssetImpairRequest,
    AssetTransferResponse,
    AssetRevaluationResponse,
)
from app.schemas.base import MessageResponse
from app.services.fixed_assets.asset_service import AssetService

router = APIRouter()


def _to_response(asset) -> FixedAssetResponse:
    """Convert model to response schema."""
    return FixedAssetResponse(
        id=asset.id,
        organization_id=asset.organization_id,
        asset_code=asset.asset_code,
        asset_name=asset.asset_name,
        description=asset.description,
        category_id=asset.category_id,
        category_code=asset.category.category_code if asset.category else None,
        category_name=asset.category.category_name if asset.category else None,
        location_id=asset.location_id,
        location_name=asset.location.name if asset.location else None,
        department_id=asset.department_id,
        department_name=asset.department.name if asset.department else None,
        custodian_employee_id=asset.custodian_employee_id,
        acquisition_date=asset.acquisition_date,
        put_to_use_date=asset.put_to_use_date,
        acquisition_type=asset.acquisition_type,
        vendor_id=asset.vendor_id,
        vendor_name=asset.vendor.name if asset.vendor else None,
        invoice_number=asset.invoice_number,
        invoice_date=asset.invoice_date,
        po_number=asset.po_number,
        acquisition_cost=asset.acquisition_cost,
        installation_cost=asset.installation_cost,
        other_costs=asset.other_costs,
        total_cost=asset.total_cost,
        residual_value=asset.residual_value,
        depreciable_value=asset.depreciable_value,
        useful_life_months=asset.useful_life_months,
        depreciation_method=asset.depreciation_method,
        depreciation_rate=asset.depreciation_rate,
        accumulated_depreciation=asset.accumulated_depreciation,
        wdv_value=asset.wdv_value,
        last_depreciation_date=asset.last_depreciation_date,
        depreciation_start_date=asset.depreciation_start_date,
        revaluation_amount=asset.revaluation_amount,
        impairment_amount=asset.impairment_amount,
        make=asset.make,
        model=asset.model,
        serial_number=asset.serial_number,
        quantity=asset.quantity,
        warranty_start_date=asset.warranty_start_date,
        warranty_expiry_date=asset.warranty_expiry_date,
        insurance_policy_number=asset.insurance_policy_number,
        insurance_provider=asset.insurance_provider,
        insurance_expiry_date=asset.insurance_expiry_date,
        insured_value=asset.insured_value,
        amc_vendor_id=asset.amc_vendor_id,
        amc_vendor_name=asset.amc_vendor.name if asset.amc_vendor else None,
        amc_start_date=asset.amc_start_date,
        amc_expiry_date=asset.amc_expiry_date,
        amc_value=asset.amc_value,
        parent_asset_id=asset.parent_asset_id,
        is_component=asset.is_component,
        disposal_date=asset.disposal_date,
        disposal_type=asset.disposal_type,
        disposal_value=asset.disposal_value,
        disposal_gain_loss=asset.disposal_gain_loss,
        disposal_remarks=asset.disposal_remarks,
        status=asset.status,
        tags=asset.tags,
        is_fully_depreciated=asset.is_fully_depreciated,
        # IT Act depreciation fields
        it_act_block=asset.it_act_block,
        it_act_rate=asset.it_act_rate,
        it_accumulated_depreciation=asset.it_accumulated_depreciation,
        it_wdv_value=asset.it_wdv_value,
        it_last_depreciation_date=asset.it_last_depreciation_date,
        it_last_depreciation_fy=asset.it_last_depreciation_fy,
        is_additional_depreciation_eligible=asset.is_additional_depreciation_eligible,
        additional_depreciation_claimed=asset.additional_depreciation_claimed,
        depreciation_difference=asset.depreciation_difference,
        is_active=asset.is_active,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        created_by=asset.created_by,
        updated_by=asset.updated_by,
    )


@router.get("", response_model=dict)
async def list_assets(
    request: Request,
    organization_id: UUID,
    category_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None,
    status: Optional[AssetStatus] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """List fixed assets with filters."""
    service = AssetService(db)
    items, total = await service.list_by_organization(
        organization_id=organization_id,
        category_id=category_id,
        location_id=location_id,
        status=status,
        search=search,
        skip=skip,
        limit=limit,
    )

    return {
        "items": [_to_response(asset) for asset in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{id}", response_model=FixedAssetResponse)
async def get_asset(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get fixed asset by ID."""
    service = AssetService(db)
    asset = await service.get(id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )
    return _to_response(asset)


@router.post("", response_model=FixedAssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    request: Request,
    data: FixedAssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_CREATE])),
):
    """Create a new fixed asset."""
    service = AssetService(db)
    try:
        asset = await service.create(data, created_by=current_user.id)
        return _to_response(asset)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/{id}", response_model=FixedAssetResponse)
async def update_asset(
    request: Request,
    id: UUID,
    data: FixedAssetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Update a fixed asset."""
    service = AssetService(db)
    try:
        asset = await service.update(id, data, updated_by=current_user.id)
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found",
            )
        return _to_response(asset)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{id}", response_model=MessageResponse)
async def delete_asset(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_DELETE])),
):
    """Delete a draft asset."""
    service = AssetService(db)
    try:
        success = await service.delete(id, deleted_by=current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found",
            )
        return MessageResponse(message="Asset deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{id}/capitalize", response_model=FixedAssetResponse)
async def capitalize_asset(
    request: Request,
    id: UUID,
    data: AssetCapitalizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_CAPITALIZE])),
):
    """Capitalize an asset (move from DRAFT to ACTIVE)."""
    service = AssetService(db)
    try:
        asset = await service.capitalize(id, data, capitalized_by=current_user.id)
        return _to_response(asset)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{id}/dispose", response_model=FixedAssetResponse)
async def dispose_asset(
    request: Request,
    id: UUID,
    data: AssetDisposeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_DISPOSE])),
):
    """Dispose an asset."""
    service = AssetService(db)
    try:
        asset = await service.dispose(id, data, disposed_by=current_user.id)
        return _to_response(asset)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{id}/transfer", response_model=AssetTransferResponse)
async def transfer_asset(
    request: Request,
    id: UUID,
    data: AssetTransferRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_TRANSFER])),
):
    """Initiate asset transfer."""
    service = AssetService(db)
    try:
        transfer = await service.transfer(id, data, transferred_by=current_user.id)
        return AssetTransferResponse(
            id=transfer.id,
            asset_id=transfer.asset_id,
            transfer_date=transfer.transfer_date,
            transfer_reference=transfer.transfer_reference,
            from_location_id=transfer.from_location_id,
            from_department_id=transfer.from_department_id,
            from_custodian_id=transfer.from_custodian_id,
            to_location_id=transfer.to_location_id,
            to_department_id=transfer.to_department_id,
            to_custodian_id=transfer.to_custodian_id,
            reason=transfer.reason,
            status=transfer.status.value,
            is_active=True,
            created_at=transfer.created_at,
            updated_at=transfer.updated_at,
            created_by=transfer.created_by,
            updated_by=transfer.updated_by,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{id}/revalue", response_model=AssetRevaluationResponse)
async def revalue_asset(
    request: Request,
    id: UUID,
    data: AssetRevalueRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_REVALUE])),
):
    """Revalue an asset."""
    service = AssetService(db)
    try:
        revaluation = await service.revalue(id, data, revalued_by=current_user.id)
        return AssetRevaluationResponse(
            id=revaluation.id,
            asset_id=revaluation.asset_id,
            revaluation_date=revaluation.revaluation_date,
            revaluation_type=revaluation.revaluation_type,
            previous_value=revaluation.previous_value,
            new_value=revaluation.new_value,
            revaluation_amount=revaluation.revaluation_amount,
            valuer_name=revaluation.valuer_name,
            valuation_report_number=revaluation.valuation_report_number,
            valuation_report_date=revaluation.valuation_report_date,
            valuation_method=revaluation.valuation_method,
            reason=revaluation.reason,
            voucher_id=revaluation.voucher_id,
            is_active=True,
            created_at=revaluation.created_at,
            updated_at=revaluation.updated_at,
            created_by=revaluation.created_by,
            updated_by=revaluation.updated_by,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{id}/impair", response_model=AssetRevaluationResponse)
async def impair_asset(
    request: Request,
    id: UUID,
    data: AssetImpairRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_REVALUE])),
):
    """Record impairment on an asset."""
    service = AssetService(db)
    try:
        revaluation = await service.impair(id, data, impaired_by=current_user.id)
        return AssetRevaluationResponse(
            id=revaluation.id,
            asset_id=revaluation.asset_id,
            revaluation_date=revaluation.revaluation_date,
            revaluation_type=revaluation.revaluation_type,
            previous_value=revaluation.previous_value,
            new_value=revaluation.new_value,
            revaluation_amount=revaluation.revaluation_amount,
            reason=revaluation.reason,
            voucher_id=revaluation.voucher_id,
            is_active=True,
            created_at=revaluation.created_at,
            updated_at=revaluation.updated_at,
            created_by=revaluation.created_by,
            updated_by=revaluation.updated_by,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
