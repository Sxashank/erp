"""Organization API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.masters.organization_service import OrganizationService
from app.schemas.masters.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
)
from app.schemas.base import PaginatedResponse, MessageResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[OrganizationResponse], response_model_by_alias=True)
async def list_organizations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    include_inactive: bool = Query(False, alias="includeInactive"),
    current_user: User = Depends(RequirePermissions("MASTER_ORG_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get paginated list of organizations.
    Requires MASTER_ORG_VIEW permission.
    """
    org_service = OrganizationService(db)
    skip = (page - 1) * page_size
    orgs, total = await org_service.get_all(skip, page_size, include_inactive)

    items = [
        OrganizationResponse(
            id=o.id,
            code=o.code,
            name=o.name,
            legal_name=o.legal_name,
            short_name=o.short_name,
            description=o.description,
            cin=o.cin,
            pan=o.pan,
            tan=o.tan,
            gstin=o.gstin,
            rbi_registration=o.rbi_registration,
            reg_address_line1=o.reg_address_line1,
            reg_address_line2=o.reg_address_line2,
            reg_city=o.reg_city,
            reg_district=o.reg_district,
            reg_state_code=o.reg_state_code,
            reg_pincode=o.reg_pincode,
            reg_country=o.reg_country,
            phone=o.phone,
            email=o.email,
            website=o.website,
            base_currency=o.base_currency,
            financial_year_start_month=o.financial_year_start_month,
            logo_path=o.logo_path,
            primary_color=o.primary_color,
            status=o.status,
            is_primary=o.is_primary,
            created_at=o.created_at,
            updated_at=o.updated_at,
            is_active=o.is_active,
        )
        for o in orgs
    ]

    return PaginatedResponse.create(items, total, page, page_size)


@router.post("", response_model=OrganizationResponse, response_model_by_alias=True)
async def create_organization(
    data: OrganizationCreate,
    current_user: User = Depends(RequirePermissions("MASTER_ORG_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Create a new organization.
    Requires MASTER_ORG_CREATE permission.
    """
    org_service = OrganizationService(db)
    org = await org_service.create(data, current_user.id)

    return await _org_to_response(org, db)


@router.get("/{org_id}", response_model=OrganizationResponse, response_model_by_alias=True)
async def get_organization(
    org_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_ORG_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get organization by ID.
    Requires MASTER_ORG_VIEW permission.
    """
    org_service = OrganizationService(db)
    result = await org_service.get(org_id)

    org = result["organization"]
    return OrganizationResponse(
        id=org.id,
        code=org.code,
        name=org.name,
        legal_name=org.legal_name,
        short_name=org.short_name,
        description=org.description,
        cin=org.cin,
        pan=org.pan,
        tan=org.tan,
        gstin=org.gstin,
        rbi_registration=org.rbi_registration,
        reg_address_line1=org.reg_address_line1,
        reg_address_line2=org.reg_address_line2,
        reg_city=org.reg_city,
        reg_district=org.reg_district,
        reg_state_code=org.reg_state_code,
        reg_pincode=org.reg_pincode,
        reg_country=org.reg_country,
        phone=org.phone,
        email=org.email,
        website=org.website,
        base_currency=org.base_currency,
        financial_year_start_month=org.financial_year_start_month,
        logo_path=org.logo_path,
        primary_color=org.primary_color,
        status=org.status,
        is_primary=org.is_primary,
        created_at=org.created_at,
        updated_at=org.updated_at,
        is_active=org.is_active,
        unit_count=result["unit_count"],
        department_count=result["department_count"],
        user_count=result["user_count"],
    )


@router.put("/{org_id}", response_model=OrganizationResponse, response_model_by_alias=True)
async def update_organization(
    org_id: UUID,
    data: OrganizationUpdate,
    current_user: User = Depends(RequirePermissions("MASTER_ORG_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Update an existing organization.
    Requires MASTER_ORG_UPDATE permission.
    """
    org_service = OrganizationService(db)
    org = await org_service.update(org_id, data, current_user.id)

    return await _org_to_response(org, db)


@router.delete("/{org_id}", response_model=MessageResponse, response_model_by_alias=True)
async def delete_organization(
    org_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_ORG_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Soft delete an organization.
    Requires MASTER_ORG_DELETE permission.
    """
    org_service = OrganizationService(db)
    await org_service.delete(org_id, current_user.id)

    return MessageResponse(message="Organization deleted successfully")


async def _org_to_response(org, db: AsyncSession) -> OrganizationResponse:
    """Convert Organization model to OrganizationResponse."""
    org_service = OrganizationService(db)
    result = await org_service.get(org.id)

    return OrganizationResponse(
        id=org.id,
        code=org.code,
        name=org.name,
        legal_name=org.legal_name,
        short_name=org.short_name,
        description=org.description,
        cin=org.cin,
        pan=org.pan,
        tan=org.tan,
        gstin=org.gstin,
        rbi_registration=org.rbi_registration,
        reg_address_line1=org.reg_address_line1,
        reg_address_line2=org.reg_address_line2,
        reg_city=org.reg_city,
        reg_district=org.reg_district,
        reg_state_code=org.reg_state_code,
        reg_pincode=org.reg_pincode,
        reg_country=org.reg_country,
        phone=org.phone,
        email=org.email,
        website=org.website,
        base_currency=org.base_currency,
        financial_year_start_month=org.financial_year_start_month,
        logo_path=org.logo_path,
        primary_color=org.primary_color,
        status=org.status,
        is_primary=org.is_primary,
        created_at=org.created_at,
        updated_at=org.updated_at,
        is_active=org.is_active,
        unit_count=result["unit_count"],
        department_count=result["department_count"],
        user_count=result["user_count"],
    )
