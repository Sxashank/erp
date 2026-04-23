"""Vendor Portal Registration Routes."""

from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.vendor_portal.registration_service import VendorRegistrationService
from app.models.vendor_portal.enums import RegistrationStatus
from app.schemas.vendor_portal.registration import (
    VendorRegistrationCreate,
    VendorRegistrationUpdate,
    VendorRegistrationResponse,
    VendorRegistrationListResponse,
    VendorRegistrationDocumentCreate,
    VendorRegistrationDocumentResponse,
    VendorRegistrationSubmit,
)

router = APIRouter()


@router.post("/", response_model=VendorRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def create_registration(
    data: VendorRegistrationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new vendor registration."""
    service = VendorRegistrationService(db)
    registration = await service.create_registration(data)
    return registration


@router.get("/{registration_id}", response_model=VendorRegistrationResponse)
async def get_registration(
    registration_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get registration details."""
    service = VendorRegistrationService(db)
    registration = await service.get_registration(registration_id)
    return registration


@router.put("/{registration_id}", response_model=VendorRegistrationResponse)
async def update_registration(
    registration_id: UUID,
    data: VendorRegistrationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a registration."""
    service = VendorRegistrationService(db)
    registration = await service.update_registration(registration_id, data)
    return registration


@router.post("/{registration_id}/documents", response_model=VendorRegistrationDocumentResponse)
async def upload_document(
    registration_id: UUID,
    document_type: str,
    document_name: str,
    file: UploadFile = File(...),
    document_number: Optional[str] = None,
    issue_date: Optional[str] = None,
    expiry_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Upload document to registration."""
    from datetime import date
    from app.models.vendor_portal.enums import RegistrationDocumentType

    service = VendorRegistrationService(db)

    # Save file (this would go to object storage in production)
    file_content = await file.read()
    file_path = f"registrations/{registration_id}/{file.filename}"
    # TODO: Implement actual file storage

    data = VendorRegistrationDocumentCreate(
        document_type=RegistrationDocumentType(document_type),
        document_name=document_name,
        document_number=document_number,
        issue_date=date.fromisoformat(issue_date) if issue_date else None,
        expiry_date=date.fromisoformat(expiry_date) if expiry_date else None,
    )

    document = await service.add_document(
        registration_id=registration_id,
        data=data,
        file_path=file_path,
        file_size=len(file_content),
        mime_type=file.content_type or "application/octet-stream",
        original_filename=file.filename or "document",
    )

    return document


@router.post("/{registration_id}/submit", response_model=VendorRegistrationResponse)
async def submit_registration(
    registration_id: UUID,
    data: VendorRegistrationSubmit,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Submit registration for review."""
    service = VendorRegistrationService(db)
    registration = await service.submit_registration(
        registration_id,
        terms_accepted=data.terms_accepted,
        terms_version=data.terms_version,
    )
    return registration


# Admin endpoints for registration review
@router.get("/", response_model=VendorRegistrationListResponse)
async def list_registrations(
    organization_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[RegistrationStatus] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all registrations (admin)."""
    service = VendorRegistrationService(db)
    registrations, total = await service.get_all_registrations(
        organization_id=organization_id,
        skip=skip,
        limit=limit,
        status=status,
        search=search,
    )
    return VendorRegistrationListResponse(
        items=registrations,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/{registration_id}/approve", response_model=VendorRegistrationResponse)
async def approve_registration(
    registration_id: UUID,
    reviewed_by: UUID,  # From auth middleware
    remarks: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Approve a registration (admin)."""
    service = VendorRegistrationService(db)
    registration = await service.approve_registration(
        registration_id,
        reviewed_by=reviewed_by,
        remarks=remarks,
    )
    return registration


@router.post("/{registration_id}/reject", response_model=VendorRegistrationResponse)
async def reject_registration(
    registration_id: UUID,
    reviewed_by: UUID,  # From auth middleware
    reason: str,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Reject a registration (admin)."""
    service = VendorRegistrationService(db)
    registration = await service.reject_registration(
        registration_id,
        reviewed_by=reviewed_by,
        reason=reason,
        category=category,
    )
    return registration


@router.post("/{registration_id}/request-info", response_model=VendorRegistrationResponse)
async def request_additional_info(
    registration_id: UUID,
    reviewed_by: UUID,  # From auth middleware
    request: str,
    db: AsyncSession = Depends(get_db),
):
    """Request additional information (admin)."""
    service = VendorRegistrationService(db)
    registration = await service.request_additional_info(
        registration_id,
        reviewed_by=reviewed_by,
        request=request,
    )
    return registration
