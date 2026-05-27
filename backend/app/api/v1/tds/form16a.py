"""Form 16A certificate API endpoints."""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_active_organization_id, get_db_with_tenant
from app.models.auth.user import User
from app.services.tds.form16a_service import Form16AService
from app.core.exceptions import NotFoundException
from app.schemas.base import CamelSchema

router = APIRouter()


class DeducteeForCertificate(CamelSchema):
    """Deductee eligible for Form 16A."""

    deductee_pan: Optional[str]
    deductee_name: str
    tds_section_id: UUID
    tds_section_code: Optional[str]
    tds_section_name: Optional[str]
    total_amount_paid: Decimal
    total_tds_deducted: Decimal
    transaction_count: int


class CertificateGenerationRequest(CamelSchema):
    """Request to generate Form 16A certificate."""

    deductee_pan: str = Field(..., max_length=10)
    tds_section_id: UUID
    financial_year: str = Field(..., max_length=10)
    quarter: str = Field(..., max_length=2, description="Q1, Q2, Q3, or Q4")


class BulkCertificateRequest(CamelSchema):
    """Request to generate bulk Form 16A certificates."""

    financial_year: str = Field(..., max_length=10)
    quarter: str = Field(..., max_length=2, description="Q1, Q2, Q3, or Q4")


class CertificateInfo(CamelSchema):
    """Certificate summary info."""

    certificate_number: str
    certificate_date: Optional[date]
    deductee_pan: Optional[str]
    deductee_name: str
    tds_section_code: Optional[str]
    tds_section_name: Optional[str]
    total_amount_paid: Decimal
    total_tds_deducted: Decimal
    entry_count: int
    artifact_status: str
    legal_status: str
    source: str
    compliance_note: Optional[str] = None


class CertificateResponse(CamelSchema):
    """Generated certificate response."""

    certificate_number: str
    deductor_tan: str
    deductor_name: str
    deductee_pan: str
    deductee_name: str
    financial_year: str
    assessment_year: str
    period_from: date
    period_to: date
    tds_section_code: str
    tds_section_name: str
    total_amount_paid: Decimal
    total_tds_deducted: Decimal
    total_tds_deposited: Decimal
    transaction_count: int
    challan_count: int
    generated_date: date
    artifact_status: str
    legal_status: str
    source: str
    compliance_note: Optional[str] = None


@router.get("/deductees", response_model=List[DeducteeForCertificate], response_model_by_alias=True)
async def get_deductees_for_certificates(
    financial_year: str = Query(...),
    quarter: str = Query(...),
    active_organization_id: UUID = Depends(get_active_organization_id),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get list of deductees eligible for Form 16A certificates."""
    service = Form16AService(db)
    deductees = await service.get_deductees_for_certificates(
        active_organization_id,
        financial_year,
        quarter,
    )
    return [DeducteeForCertificate(**d) for d in deductees]


@router.post("/generate", response_model=CertificateResponse, response_model_by_alias=True)
async def generate_certificate(
    data: CertificateGenerationRequest,
    active_organization_id: UUID = Depends(get_active_organization_id),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Generate Form 16A certificate for a deductee."""
    service = Form16AService(db)
    cert = await service.generate_certificate(
        active_organization_id,
        data.deductee_pan,
        data.tds_section_id,
        data.financial_year,
        data.quarter,
    )
    return CertificateResponse(
        certificate_number=cert.certificate_number,
        deductor_tan=cert.deductor_tan,
        deductor_name=cert.deductor_name,
        deductee_pan=cert.deductee_pan,
        deductee_name=cert.deductee_name,
        financial_year=cert.financial_year,
        assessment_year=cert.assessment_year,
        period_from=cert.period_from,
        period_to=cert.period_to,
        tds_section_code=cert.tds_section_code,
        tds_section_name=cert.tds_section_name,
        total_amount_paid=cert.total_amount_paid,
        total_tds_deducted=cert.total_tds_deducted,
        total_tds_deposited=cert.total_tds_deposited,
        transaction_count=len(cert.transactions),
        challan_count=len(cert.challans),
        generated_date=cert.generated_date,
        artifact_status=service.WORKING_SUMMARY_STATUS,
        legal_status=service.LEGAL_STATUS,
        source=service.SOURCE,
        compliance_note=service.COMPLIANCE_NOTE,
    )


@router.post(
    "/generate-bulk", response_model=List[CertificateResponse], response_model_by_alias=True
)
async def generate_bulk_certificates(
    data: BulkCertificateRequest,
    active_organization_id: UUID = Depends(get_active_organization_id),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Generate Form 16A certificates for all eligible deductees."""
    service = Form16AService(db)
    certificates = await service.generate_bulk_certificates(
        active_organization_id,
        data.financial_year,
        data.quarter,
    )
    return [
        CertificateResponse(
            certificate_number=cert.certificate_number,
            deductor_tan=cert.deductor_tan,
            deductor_name=cert.deductor_name,
            deductee_pan=cert.deductee_pan,
            deductee_name=cert.deductee_name,
            financial_year=cert.financial_year,
            assessment_year=cert.assessment_year,
            period_from=cert.period_from,
            period_to=cert.period_to,
            tds_section_code=cert.tds_section_code,
            tds_section_name=cert.tds_section_name,
            total_amount_paid=cert.total_amount_paid,
            total_tds_deducted=cert.total_tds_deducted,
            total_tds_deposited=cert.total_tds_deposited,
            transaction_count=len(cert.transactions),
            challan_count=len(cert.challans),
            generated_date=cert.generated_date,
            artifact_status=service.WORKING_SUMMARY_STATUS,
            legal_status=service.LEGAL_STATUS,
            source=service.SOURCE,
            compliance_note=service.COMPLIANCE_NOTE,
        )
        for cert in certificates
    ]


@router.get("/download/{certificate_number}")
async def download_certificate(
    certificate_number: str,
    active_organization_id: UUID = Depends(get_active_organization_id),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Download Form 16A certificate as HTML/PDF."""
    service = Form16AService(db)

    # Get certificate data
    cert_info = await service.get_certificate_by_number(
        active_organization_id,
        certificate_number,
    )

    if not cert_info:
        raise NotFoundException(detail="Certificate not found", error_code="CERTIFICATE_NOT_FOUND")

    # Generate full certificate (need to regenerate to get all data)
    # In production, you'd store the certificate data
    # For now, we return the basic info as HTML

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Form 16A - {certificate_number}</title>
    </head>
    <body>
        <h1>Form 16A Certificate</h1>
        <p><strong>Certificate Number:</strong> {cert_info['certificate_number']}</p>
        <p><strong>Deductee:</strong> {cert_info['deductee_name']} ({cert_info['deductee_pan']})</p>
        <p><strong>Total Amount Paid:</strong> Rs. {cert_info['total_amount_paid']:,.2f}</p>
        <p><strong>Total TDS Deducted:</strong> Rs. {cert_info['total_tds_deducted']:,.2f}</p>
        <p><strong>Entries:</strong> {cert_info['entry_count']}</p>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@router.get("/list", response_model=List[CertificateInfo], response_model_by_alias=True)
async def list_certificates(
    financial_year: str = Query(...),
    quarter: Optional[str] = Query(None),
    active_organization_id: UUID = Depends(get_active_organization_id),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get list of generated certificates."""
    service = Form16AService(db)
    certificates = await service.get_generated_certificates(
        active_organization_id,
        financial_year,
        quarter,
    )
    return [CertificateInfo(**c) for c in certificates]


@router.get("/{certificate_number}", response_model=CertificateInfo, response_model_by_alias=True)
async def get_certificate(
    certificate_number: str,
    active_organization_id: UUID = Depends(get_active_organization_id),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get certificate details by number."""
    service = Form16AService(db)
    cert = await service.get_certificate_by_number(
        active_organization_id,
        certificate_number,
    )

    if not cert:
        raise NotFoundException(detail="Certificate not found", error_code="CERTIFICATE_NOT_FOUND")

    return CertificateInfo(**cert)
