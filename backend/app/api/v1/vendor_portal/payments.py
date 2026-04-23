"""Vendor Portal Payment Routes."""

from datetime import date
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.vendor_portal.payment_service import VendorPaymentService
from app.schemas.vendor_portal.payment import (
    VendorPaymentListResponse,
    VendorPaymentResponse,
    VendorPaymentFilter,
    VendorAgingFilter,
    VendorAgingReport,
    VendorStatementFilter,
    VendorStatement,
    VendorPaymentSummary,
    UpcomingPayment,
)

router = APIRouter()


@router.get("/", response_model=VendorPaymentListResponse)
async def list_payments(
    vendor_id: UUID,  # From auth middleware
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List payments for vendor."""
    service = VendorPaymentService(db)

    filters = VendorPaymentFilter(
        from_date=from_date,
        to_date=to_date,
        status=status,
    ) if any([from_date, to_date, status]) else None

    payments, total = await service.get_payments(
        vendor_id=vendor_id,
        skip=skip,
        limit=limit,
        filters=filters,
    )
    return VendorPaymentListResponse(
        items=payments,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/summary", response_model=VendorPaymentSummary)
async def get_payment_summary(
    vendor_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get payment summary for dashboard."""
    service = VendorPaymentService(db)
    summary = await service.get_payment_summary(vendor_id)
    return summary


@router.get("/upcoming")
async def get_upcoming_payments(
    vendor_id: UUID,  # From auth middleware
    days: int = Query(30, ge=1, le=180),
    db: AsyncSession = Depends(get_db),
):
    """Get upcoming payments (invoices due soon)."""
    service = VendorPaymentService(db)
    upcoming = await service.get_upcoming_payments(vendor_id, days)
    return upcoming


@router.get("/aging", response_model=VendorAgingReport)
async def get_aging_report(
    vendor_id: UUID,  # From auth middleware
    as_of_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get aging report."""
    service = VendorPaymentService(db)

    filters = VendorAgingFilter(as_of_date=as_of_date) if as_of_date else None
    aging = await service.get_aging_report(vendor_id, filters)
    return aging


@router.get("/statement", response_model=VendorStatement)
async def get_account_statement(
    vendor_id: UUID,  # From auth middleware
    from_date: date,
    to_date: date,
    db: AsyncSession = Depends(get_db),
):
    """Get account statement."""
    service = VendorPaymentService(db)

    filters = VendorStatementFilter(from_date=from_date, to_date=to_date)
    statement = await service.get_account_statement(vendor_id, filters)
    return statement


@router.get("/statement/download")
async def download_statement_pdf(
    vendor_id: UUID,  # From auth middleware
    from_date: date,
    to_date: date,
    db: AsyncSession = Depends(get_db),
):
    """Download account statement as PDF."""
    service = VendorPaymentService(db)

    filters = VendorStatementFilter(from_date=from_date, to_date=to_date)
    pdf_bytes = await service.download_statement_pdf(vendor_id, filters)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=statement_{from_date}_{to_date}.pdf"
        },
    )


@router.get("/{payment_id}", response_model=VendorPaymentResponse)
async def get_payment(
    vendor_id: UUID,  # From auth middleware
    payment_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get payment details."""
    service = VendorPaymentService(db)
    payment = await service.get_payment_details(vendor_id, payment_id)
    return payment


@router.get("/{payment_id}/remittance")
async def get_remittance_advice(
    vendor_id: UUID,  # From auth middleware
    payment_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get remittance advice for a payment."""
    service = VendorPaymentService(db)
    remittance = await service.get_remittance_advice(vendor_id, payment_id)
    return remittance


@router.get("/{payment_id}/remittance/download")
async def download_remittance_pdf(
    vendor_id: UUID,  # From auth middleware
    payment_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Download remittance advice as PDF."""
    service = VendorPaymentService(db)
    pdf_bytes = await service.download_remittance_pdf(vendor_id, payment_id)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=remittance_{payment_id}.pdf"
        },
    )
