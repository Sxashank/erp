"""Certificate API endpoints — admin (issue / list) and download."""

from __future__ import annotations

import os
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.core.exceptions import NotFoundException
from app.schemas.lending.certificates import (
    CertificateListResponse,
    CertificateResponse,
    IssueForeclosureLetterRequest,
    IssueNdcRequest,
)
from app.services.lending.certificate_service import CertificateService

router = APIRouter()


@router.get(
    "/loan-accounts/{loan_account_id}/certificates",
    response_model=CertificateListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_READ"))],
)
async def list_loan_certificates(
    loan_account_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> CertificateListResponse:
    service = CertificateService(db)
    rows = await service.list_for_loan(
        organization_id=current_user.organization_id,
        loan_account_id=loan_account_id,
    )
    return CertificateListResponse(
        items=[CertificateResponse.model_validate(r) for r in rows],
        total=len(rows),
    )


@router.get(
    "/applications/{application_id}/certificates",
    response_model=CertificateListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LOS_READ"))],
)
async def list_application_certificates(
    application_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> CertificateListResponse:
    service = CertificateService(db)
    rows = await service.list_for_application(
        organization_id=current_user.organization_id,
        application_id=application_id,
    )
    return CertificateListResponse(
        items=[CertificateResponse.model_validate(r) for r in rows],
        total=len(rows),
    )


@router.post(
    "/loan-accounts/{loan_account_id}/certificates/ndc",
    response_model=CertificateResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_WRITE"))],
)
async def issue_ndc(
    loan_account_id: UUID,
    data: IssueNdcRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> CertificateResponse:
    from app.models.lending.entity import Entity
    from app.models.lending.loan_account import LoanAccount
    from app.models.masters.organization import Organization

    loan = await db.get(LoanAccount, loan_account_id)
    if loan is None or loan.organization_id != current_user.organization_id:
        raise NotFoundException(
            detail=f"Loan account {loan_account_id} not found",
            error_code="LOAN_ACCOUNT_NOT_FOUND",
        )
    entity = await db.get(Entity, loan.entity_id) if getattr(loan, "entity_id", None) else None
    organization = await db.get(Organization, current_user.organization_id)

    async with db.begin():
        service = CertificateService(db)
        cert = await service.issue_ndc(
            organization_id=current_user.organization_id,
            loan_account_id=loan_account_id,
            issued_by_id=current_user.id,
            organization_name=organization.name if organization else "—",
            organization_address=(
                getattr(organization, "registered_address", None) if organization else None
            ),
            borrower_name=entity.legal_name if entity else "Borrower",
            loan_account_number=loan.loan_account_number or str(loan.id)[:8],
            closure_date=data.closure_date,
            period_start=data.period_start,
        )
    await db.refresh(cert)
    return CertificateResponse.model_validate(cert)


@router.post(
    "/loan-accounts/{loan_account_id}/certificates/foreclosure-letter",
    response_model=CertificateResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_WRITE"))],
)
async def issue_foreclosure_letter(
    loan_account_id: UUID,
    data: IssueForeclosureLetterRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> CertificateResponse:
    from app.models.lending.entity import Entity
    from app.models.lending.loan_account import LoanAccount
    from app.models.masters.organization import Organization

    loan = await db.get(LoanAccount, loan_account_id)
    if loan is None or loan.organization_id != current_user.organization_id:
        raise NotFoundException(
            detail=f"Loan account {loan_account_id} not found",
            error_code="LOAN_ACCOUNT_NOT_FOUND",
        )
    entity = await db.get(Entity, loan.entity_id) if getattr(loan, "entity_id", None) else None
    organization = await db.get(Organization, current_user.organization_id)

    async with db.begin():
        service = CertificateService(db)
        cert = await service.issue_foreclosure_letter(
            organization_id=current_user.organization_id,
            loan_account_id=loan_account_id,
            issued_by_id=current_user.id,
            organization_name=organization.name if organization else "—",
            organization_address=(
                getattr(organization, "registered_address", None) if organization else None
            ),
            borrower_name=entity.legal_name if entity else "Borrower",
            loan_account_number=loan.loan_account_number or str(loan.id)[:8],
            as_of_date=data.as_of_date,
            valid_till=data.valid_till,
            principal_outstanding=Decimal(data.principal_outstanding),
            interest_accrued=Decimal(data.interest_accrued),
            foreclosure_fee=Decimal(data.foreclosure_fee),
            other_charges=Decimal(data.other_charges),
            payment_account_details=data.payment_account_details,
        )
    await db.refresh(cert)
    return CertificateResponse.model_validate(cert)


@router.get(
    "/certificates/{certificate_id}/download",
    dependencies=[Depends(RequirePermissions("LMS_READ"))],
)
async def download_certificate(
    certificate_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Streams the PDF file. File path is the DMS storage path."""
    service = CertificateService(db)
    cert = await service.get(
        organization_id=current_user.organization_id,
        certificate_id=certificate_id,
    )
    if cert.file_path is None or not os.path.exists(cert.file_path):
        raise NotFoundException(
            detail="Certificate PDF file not found on disk",
            error_code="CERTIFICATE_FILE_MISSING",
        )
    return FileResponse(
        cert.file_path,
        media_type="application/pdf",
        filename=f"{cert.certificate_type.value}_{cert.certificate_number}.pdf",
    )
