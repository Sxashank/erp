"""Portal Document API endpoints."""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.v1.portal.auth import get_portal_user
from app.models.portal.enums import PortalDocumentType, KYCType
from app.services.portal.document_service import PortalDocumentService

router = APIRouter(prefix="/documents", tags=["Portal Documents"])


# =============================================================================
# Response Schemas
# =============================================================================


class DocumentResponse(BaseModel):
    """Document response."""

    id: str
    document_type: str
    document_name: str
    description: Optional[str] = None
    file_name: str
    file_type: str
    file_size: int
    document_date: Optional[str] = None
    is_downloadable: bool
    requires_otp: bool


class DocumentRequestCreate(BaseModel):
    """Create document request."""

    loan_account_id: Optional[UUID] = None
    document_type: PortalDocumentType
    reason: Optional[str] = None
    delivery_mode: str = "DOWNLOAD"
    delivery_email: Optional[str] = None
    delivery_address: Optional[str] = None
    period_from: Optional[date] = None
    period_to: Optional[date] = None
    financial_year: Optional[str] = None


class DocumentRequestResponse(BaseModel):
    """Document request response."""

    id: str
    request_number: str
    document_type: str
    status: str
    status_message: Optional[str] = None
    created_at: str
    fulfilled_at: Optional[str] = None


class KYCInitiateRequest(BaseModel):
    """Initiate KYC request."""

    kyc_type: KYCType
    aadhaar_last4: Optional[str] = Field(None, min_length=4, max_length=4)
    pan_number: Optional[str] = Field(None, min_length=10, max_length=10)
    name_to_match: Optional[str] = None
    consent_text: str


class KYCVerifyOTPRequest(BaseModel):
    """Verify KYC OTP request."""

    kyc_id: UUID
    otp: str = Field(..., min_length=4, max_length=8)


class KYCResponse(BaseModel):
    """KYC response."""

    kyc_id: str
    reference_number: str
    status: str
    otp_sent: Optional[bool] = None
    expires_at: Optional[str] = None
    verified_data: Optional[dict] = None


class KYCHistoryItem(BaseModel):
    """KYC history item."""

    id: str
    kyc_type: str
    reference_number: str
    status: str
    initiated_at: str
    completed_at: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Paginated response."""

    items: List
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Document Access
# =============================================================================


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="Get Documents",
)
async def get_documents(
    loan_account_id: Optional[UUID] = None,
    document_type: Optional[PortalDocumentType] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Get documents available to the customer."""
    service = PortalDocumentService(db)
    items, total = await service.get_documents(
        user_id=user.id,
        loan_account_id=loan_account_id,
        document_type=document_type,
        page=page,
        page_size=page_size,
    )

    return PaginatedResponse(
        items=[DocumentResponse(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get Document Details",
)
async def get_document(
    document_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document details."""
    service = PortalDocumentService(db)
    document = await service.get_document(document_id, user.id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Record view
    await service.record_view(document_id, user.id)
    await db.commit()

    return DocumentResponse(
        id=str(document.id),
        document_type=document.document_type.value,
        document_name=document.document_name,
        description=document.description,
        file_name=document.file_name,
        file_type=document.file_type,
        file_size=document.file_size,
        document_date=document.document_date.isoformat() if document.document_date else None,
        is_downloadable=document.is_downloadable,
        requires_otp=document.requires_otp,
    )


@router.get(
    "/{document_id}/download",
    summary="Download Document",
)
async def download_document(
    document_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a document."""
    service = PortalDocumentService(db)
    result = await service.download_document(document_id, user.id)
    await db.commit()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result["error"],
        )

    # In production, this would stream the file from storage
    # Placeholder: Return file info
    return {
        "file_path": result["file_path"],
        "file_name": result["file_name"],
        "message": "File would be streamed from storage",
    }


# =============================================================================
# Document Generation
# =============================================================================


@router.get(
    "/statement",
    summary="Generate Account Statement",
)
async def generate_statement(
    loan_account_id: UUID,
    from_date: date,
    to_date: date,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate and download account statement.

    Statement is available for download immediately.
    """
    service = PortalDocumentService(db)
    document = await service.generate_account_statement(
        organization_id=user.organization_id,
        user_id=user.id,
        loan_account_id=loan_account_id,
        from_date=from_date,
        to_date=to_date,
    )
    await db.commit()

    return {
        "document_id": str(document.id),
        "document_name": document.document_name,
        "message": "Statement generated successfully",
    }


@router.get(
    "/interest-cert",
    summary="Generate Interest Certificate",
)
async def generate_interest_certificate(
    loan_account_id: UUID,
    financial_year: str = Query(..., description="Format: 2023-24"),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate interest certificate for tax purposes.

    Used for claiming tax deduction under Section 80EE/80EEA.
    """
    service = PortalDocumentService(db)
    document = await service.generate_interest_certificate(
        organization_id=user.organization_id,
        user_id=user.id,
        loan_account_id=loan_account_id,
        financial_year=financial_year,
    )
    await db.commit()

    return {
        "document_id": str(document.id),
        "document_name": document.document_name,
        "message": "Interest certificate generated successfully",
    }


@router.get(
    "/tds-cert",
    summary="Generate TDS Certificate",
)
async def generate_tds_certificate(
    loan_account_id: UUID,
    financial_year: str = Query(..., description="Format: 2023-24"),
    quarter: str = Query(..., description="Q1, Q2, Q3, Q4"),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate TDS certificate (Form 16A).

    Available for deposits where TDS has been deducted.
    """
    service = PortalDocumentService(db)
    document = await service.generate_tds_certificate(
        organization_id=user.organization_id,
        user_id=user.id,
        loan_account_id=loan_account_id,
        financial_year=financial_year,
        quarter=quarter,
    )
    await db.commit()

    return {
        "document_id": str(document.id),
        "document_name": document.document_name,
        "message": "TDS certificate generated successfully",
    }


# =============================================================================
# Document Requests
# =============================================================================


@router.post(
    "/requests",
    response_model=DocumentRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request Document",
)
async def create_document_request(
    request: DocumentRequestCreate,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Request a document.

    Used for documents that require processing like NOC, physical statements.
    """
    service = PortalDocumentService(db)
    doc_request = await service.create_document_request(
        organization_id=user.organization_id,
        user_id=user.id,
        **request.model_dump(),
    )
    await db.commit()

    return DocumentRequestResponse(
        id=str(doc_request.id),
        request_number=doc_request.request_number,
        document_type=doc_request.document_type.value,
        status=doc_request.status.value,
        status_message=doc_request.status_message,
        created_at=doc_request.created_at.isoformat(),
        fulfilled_at=None,
    )


@router.get(
    "/requests",
    response_model=PaginatedResponse,
    summary="Get Document Requests",
)
async def get_document_requests(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document requests."""
    service = PortalDocumentService(db)
    items, total = await service.get_document_requests(
        user_id=user.id,
        status=status,
        page=page,
        page_size=page_size,
    )

    return PaginatedResponse(
        items=[DocumentRequestResponse(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.get(
    "/requests/{request_id}",
    response_model=DocumentRequestResponse,
    summary="Get Document Request Status",
)
async def get_document_request(
    request_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document request status."""
    service = PortalDocumentService(db)
    doc_request = await service.get_document_request(request_id, user.id)

    if not doc_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document request not found",
        )

    return DocumentRequestResponse(
        id=str(doc_request.id),
        request_number=doc_request.request_number,
        document_type=doc_request.document_type.value,
        status=doc_request.status.value,
        status_message=doc_request.status_message,
        created_at=doc_request.created_at.isoformat(),
        fulfilled_at=doc_request.fulfilled_at.isoformat() if doc_request.fulfilled_at else None,
    )


# =============================================================================
# KYC Verification
# =============================================================================


@router.post(
    "/kyc/aadhaar",
    response_model=KYCResponse,
    summary="Initiate Aadhaar eKYC",
)
async def initiate_aadhaar_kyc(
    request: KYCInitiateRequest,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate Aadhaar eKYC verification.

    Sends OTP to Aadhaar-linked mobile number.
    """
    if request.kyc_type != KYCType.AADHAAR_OTP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use this endpoint only for Aadhaar OTP KYC",
        )

    if not request.aadhaar_last4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aadhaar last 4 digits required",
        )

    service = PortalDocumentService(db)
    result = await service.initiate_aadhaar_kyc(
        organization_id=user.organization_id,
        user_id=user.id,
        customer_id=user.customer_id,
        aadhaar_last4=request.aadhaar_last4,
        consent_text=request.consent_text,
    )
    await db.commit()

    return KYCResponse(**result)


@router.post(
    "/kyc/aadhaar/verify",
    response_model=KYCResponse,
    summary="Verify Aadhaar OTP",
)
async def verify_aadhaar_otp(
    request: KYCVerifyOTPRequest,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify Aadhaar OTP and complete eKYC."""
    service = PortalDocumentService(db)
    result = await service.verify_aadhaar_otp(
        kyc_id=request.kyc_id,
        user_id=user.id,
        otp=request.otp,
    )
    await db.commit()

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error"),
        )

    return KYCResponse(
        kyc_id=result.get("kyc_id"),
        reference_number="",
        status="COMPLETED",
        verified_data=result.get("verified_data"),
    )


@router.post(
    "/kyc/pan",
    response_model=KYCResponse,
    summary="Verify PAN",
)
async def verify_pan(
    request: KYCInitiateRequest,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify PAN number.

    Validates PAN and matches name with records.
    """
    if request.kyc_type != KYCType.PAN_VERIFICATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use this endpoint only for PAN verification",
        )

    if not request.pan_number or not request.name_to_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PAN number and name required",
        )

    service = PortalDocumentService(db)
    result = await service.initiate_pan_verification(
        organization_id=user.organization_id,
        user_id=user.id,
        customer_id=user.customer_id,
        pan_number=request.pan_number,
        name_to_match=request.name_to_match,
    )
    await db.commit()

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error"),
        )

    return KYCResponse(
        kyc_id=result.get("kyc_id"),
        reference_number="",
        status="COMPLETED",
        verified_data={
            "verified": result.get("verified"),
            "name_match": result.get("name_match"),
        },
    )


@router.get(
    "/kyc/history",
    response_model=List[KYCHistoryItem],
    summary="Get KYC History",
)
async def get_kyc_history(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Get KYC verification history."""
    service = PortalDocumentService(db)
    history = await service.get_kyc_history(
        user_id=user.id,
        customer_id=user.customer_id,
    )

    return [KYCHistoryItem(**item) for item in history]
