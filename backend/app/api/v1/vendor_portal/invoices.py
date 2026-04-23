"""Vendor Portal Invoice Routes."""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.vendor_portal.invoice_service import VendorInvoiceService
from app.models.vendor_portal.enums import VendorInvoiceStatus, InvoiceDocumentType
from app.schemas.vendor_portal.invoice import (
    VendorInvoiceCreate,
    VendorInvoiceUpdate,
    VendorInvoiceResponse,
    VendorInvoiceListResponse,
    VendorInvoiceLineCreate,
    VendorInvoiceLineResponse,
    VendorInvoiceDocumentCreate,
    VendorInvoiceDocumentResponse,
    InvoiceMatchingResult,
)

router = APIRouter()


@router.get("/", response_model=VendorInvoiceListResponse)
async def list_invoices(
    vendor_id: UUID,  # From auth middleware
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[VendorInvoiceStatus] = None,
    db: AsyncSession = Depends(get_db),
):
    """List invoices for vendor."""
    service = VendorInvoiceService(db)
    invoices, total = await service.get_vendor_invoices(
        vendor_id=vendor_id,
        skip=skip,
        limit=limit,
        status=status,
    )
    return VendorInvoiceListResponse(
        items=invoices,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/", response_model=VendorInvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    vendor_id: UUID,  # From auth middleware
    organization_id: UUID,  # From auth middleware
    user_id: UUID,  # From auth middleware
    data: VendorInvoiceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new invoice draft."""
    service = VendorInvoiceService(db)
    invoice = await service.create_invoice(
        vendor_id=vendor_id,
        organization_id=organization_id,
        submitted_by_id=user_id,
        data=data,
    )
    return invoice


@router.get("/{invoice_id}", response_model=VendorInvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get invoice details."""
    service = VendorInvoiceService(db)
    invoice = await service.get_invoice(invoice_id)
    return invoice


@router.put("/{invoice_id}", response_model=VendorInvoiceResponse)
async def update_invoice(
    invoice_id: UUID,
    data: VendorInvoiceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update an invoice draft."""
    service = VendorInvoiceService(db)
    invoice = await service.update_invoice(invoice_id, data)
    return invoice


@router.post("/{invoice_id}/lines", response_model=VendorInvoiceLineResponse)
async def add_invoice_line(
    invoice_id: UUID,
    data: VendorInvoiceLineCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add line item to invoice."""
    service = VendorInvoiceService(db)
    line = await service.add_line(invoice_id, data)
    return line


@router.post("/{invoice_id}/documents", response_model=VendorInvoiceDocumentResponse)
async def upload_invoice_document(
    invoice_id: UUID,
    document_type: str,
    document_name: str,
    file: UploadFile = File(...),
    document_number: Optional[str] = None,
    document_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Upload document to invoice."""
    from datetime import date

    service = VendorInvoiceService(db)

    # Save file (this would go to object storage in production)
    file_content = await file.read()
    file_path = f"invoices/{invoice_id}/{file.filename}"
    # TODO: Implement actual file storage

    data = VendorInvoiceDocumentCreate(
        document_type=InvoiceDocumentType(document_type),
        document_name=document_name,
        document_number=document_number,
        document_date=date.fromisoformat(document_date) if document_date else None,
    )

    document = await service.add_document(
        invoice_id=invoice_id,
        data=data,
        file_path=file_path,
        file_size=len(file_content),
        mime_type=file.content_type or "application/octet-stream",
        original_filename=file.filename or "document",
    )

    return document


@router.post("/{invoice_id}/validate", response_model=InvoiceMatchingResult)
async def validate_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Validate invoice using matching engine."""
    service = VendorInvoiceService(db)
    result = await service.validate_invoice(invoice_id)
    return result


@router.post("/{invoice_id}/submit", response_model=VendorInvoiceResponse)
async def submit_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Submit invoice for approval."""
    service = VendorInvoiceService(db)
    invoice = await service.submit_invoice(invoice_id)
    return invoice


# Admin endpoints for invoice approval
@router.post("/{invoice_id}/approve", response_model=VendorInvoiceResponse)
async def approve_invoice(
    invoice_id: UUID,
    user_id: UUID,  # From auth middleware (approver)
    remarks: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Approve an invoice (admin)."""
    service = VendorInvoiceService(db)
    invoice = await service.approve_invoice(invoice_id, user_id, remarks)
    return invoice


@router.post("/{invoice_id}/reject", response_model=VendorInvoiceResponse)
async def reject_invoice(
    invoice_id: UUID,
    user_id: UUID,  # From auth middleware (rejector)
    reason: str,
    db: AsyncSession = Depends(get_db),
):
    """Reject an invoice (admin)."""
    service = VendorInvoiceService(db)
    invoice = await service.reject_invoice(invoice_id, user_id, reason)
    return invoice
