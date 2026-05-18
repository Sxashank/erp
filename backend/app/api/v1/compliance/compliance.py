"""
Compliance API Endpoints
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.compliance.compliance import (
    ComplianceItemCreate,
    ComplianceItemUpdate,
    ComplianceItemResponse,
    ComplianceItemList,
    ComplianceInstanceCreate,
    ComplianceInstanceUpdate,
    ComplianceInstanceResponse,
    ComplianceInstanceList,
    ComplianceDocumentCreate,
    ComplianceDocumentResponse,
    ComplianceSummary,
    UpcomingCompliance,
)
from app.services.compliance.compliance_service import (
    ComplianceItemService,
    ComplianceInstanceService,
    ComplianceDocumentService,
)
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter()


# ============== Compliance Items (Master) ==============

@router.get("/items", response_model=dict, response_model_by_alias=True)
async def list_compliance_items(
    regulatory_body: Optional[str] = Query(None),
    frequency: Optional[str] = Query(None),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List compliance items for an organization"""
    service = ComplianceItemService(db)
    items, total = await service.list(
        organization_id=current_user.organization_id,
        regulatory_body=regulatory_body,
        frequency=frequency,
        active_only=active_only,
        skip=skip,
        limit=limit
    )
    return {
        "items": [ComplianceItemList.model_validate(item) for item in items],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/items", response_model=ComplianceItemResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_compliance_item(
    data: ComplianceItemCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create a new compliance item"""
    # Force tenant scope from the JWT — never trust the body's organization_id.
    data.organization_id = current_user.organization_id
    service = ComplianceItemService(db)

    # Check for duplicate code
    existing = await service.get_by_code(current_user.organization_id, data.item_code)
    if existing:
        raise BadRequestException(
            detail=f"Item with code {data.item_code} already exists",
            error_code="ITEM_WITH_CODE_ALREADY_EXISTS",
        )

    item = await service.create(data, current_user.id)
    return ComplianceItemResponse.model_validate(item)


@router.get("/items/{id}", response_model=ComplianceItemResponse, response_model_by_alias=True)
async def get_compliance_item(
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get compliance item by ID"""
    service = ComplianceItemService(db)
    item = await service.get(id)
    if not item:
        raise NotFoundException(detail="Item not found", error_code="ITEM_NOT_FOUND")
    return ComplianceItemResponse.model_validate(item)


@router.put("/items/{id}", response_model=ComplianceItemResponse, response_model_by_alias=True)
async def update_compliance_item(
    id: UUID,
    data: ComplianceItemUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Update a compliance item"""
    service = ComplianceItemService(db)
    item = await service.update(id, data, current_user.id)
    if not item:
        raise NotFoundException(detail="Item not found", error_code="ITEM_NOT_FOUND")
    return ComplianceItemResponse.model_validate(item)


@router.delete("/items/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_compliance_item(
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Delete (deactivate) a compliance item"""
    service = ComplianceItemService(db)
    deleted = await service.delete(id)
    if not deleted:
        raise NotFoundException(detail="Item not found", error_code="ITEM_NOT_FOUND")


# ============== Compliance Instances ==============

@router.get("/instances", response_model=dict, response_model_by_alias=True)
async def list_compliance_instances(
    compliance_item_id: Optional[UUID] = Query(None),
    regulatory_body: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List compliance instances"""
    service = ComplianceInstanceService(db)
    items, total = await service.list(
        organization_id=current_user.organization_id,
        compliance_item_id=compliance_item_id,
        regulatory_body=regulatory_body,
        status=status,
        year=year,
        month=month,
        skip=skip,
        limit=limit
    )
    result = []
    for item in items:
        instance_dict = ComplianceInstanceList.model_validate(item).model_dump()
        if item.compliance_item:
            instance_dict['item_code'] = item.compliance_item.item_code
            instance_dict['item_name'] = item.compliance_item.item_name
            instance_dict['regulatory_body'] = item.compliance_item.regulatory_body
        result.append(instance_dict)
    return {
        "items": result,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/instances", response_model=ComplianceInstanceResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_compliance_instance(
    data: ComplianceInstanceCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create a new compliance instance"""
    service = ComplianceInstanceService(db)
    instance = await service.create(data, current_user.id)
    return ComplianceInstanceResponse.model_validate(instance)


@router.get("/instances/{id}", response_model=ComplianceInstanceResponse, response_model_by_alias=True)
async def get_compliance_instance(
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get compliance instance by ID"""
    service = ComplianceInstanceService(db)
    instance = await service.get(id)
    if not instance:
        raise NotFoundException(detail="Instance not found", error_code="INSTANCE_NOT_FOUND")
    return ComplianceInstanceResponse.model_validate(instance)


@router.put("/instances/{id}", response_model=ComplianceInstanceResponse, response_model_by_alias=True)
async def update_compliance_instance(
    id: UUID,
    data: ComplianceInstanceUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Update a compliance instance"""
    service = ComplianceInstanceService(db)
    instance = await service.update(id, data, current_user.id)
    if not instance:
        raise NotFoundException(detail="Instance not found", error_code="INSTANCE_NOT_FOUND")
    return ComplianceInstanceResponse.model_validate(instance)


@router.post("/instances/{id}/file", response_model=ComplianceInstanceResponse, response_model_by_alias=True)
async def mark_instance_filed(
    id: UUID,
    acknowledgment_number: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Mark compliance instance as filed"""
    service = ComplianceInstanceService(db)
    data = ComplianceInstanceUpdate(
        status="FILED",
        acknowledgment_number=acknowledgment_number
    )
    instance = await service.update(id, data, current_user.id)
    if not instance:
        raise NotFoundException(detail="Instance not found", error_code="INSTANCE_NOT_FOUND")
    return ComplianceInstanceResponse.model_validate(instance)


# ============== Dashboard & Summary ==============

@router.get("/summary", response_model=ComplianceSummary, response_model_by_alias=True)
async def get_compliance_summary(
    year: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get compliance summary for dashboard"""
    service = ComplianceInstanceService(db)
    return await service.get_summary(current_user.organization_id, year)


@router.get("/upcoming", response_model=UpcomingCompliance, response_model_by_alias=True)
async def get_upcoming_compliance(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get upcoming compliance items"""
    service = ComplianceInstanceService(db)
    return await service.get_upcoming(current_user.organization_id)


@router.post("/generate-instances")
async def generate_compliance_instances(
    year: int = Query(...),
    month: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Generate compliance instances for a period"""
    service = ComplianceInstanceService(db)
    instances = await service.generate_instances_for_period(
        organization_id=current_user.organization_id,
        year=year,
        month=month,
        created_by=current_user.id
    )
    return {
        "message": f"Generated {len(instances)} compliance instances",
        "count": len(instances)
    }


# ============== Documents ==============

@router.get("/instances/{instance_id}/documents", response_model=List[ComplianceDocumentResponse], response_model_by_alias=True)
async def list_instance_documents(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List documents for a compliance instance"""
    service = ComplianceDocumentService(db)
    docs = await service.list_by_instance(instance_id)
    return [ComplianceDocumentResponse.model_validate(doc) for doc in docs]


@router.post("/documents", response_model=ComplianceDocumentResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def upload_compliance_document(
    data: ComplianceDocumentCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Upload a document for compliance instance"""
    service = ComplianceDocumentService(db)
    doc = await service.create(data, current_user.id)
    return ComplianceDocumentResponse.model_validate(doc)


@router.delete("/documents/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_compliance_document(
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Delete a compliance document"""
    service = ComplianceDocumentService(db)
    deleted = await service.delete(id)
    if not deleted:
        raise NotFoundException(detail="Document not found", error_code="DOCUMENT_NOT_FOUND")
