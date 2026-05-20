"""Portal Service Request API endpoints."""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, status, Query, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.v1.portal.auth import get_portal_db_with_tenant, get_portal_user
from app.models.portal.enums import ServiceRequestType, ServiceRequestStatus
from app.services.portal.service_request_service import PortalServiceRequestService
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter(prefix="/service-requests", tags=["Portal Service Requests"])


# =============================================================================
# Request/Response Schemas
# =============================================================================


class ServiceRequestCreate(BaseModel):
    """Create service request."""

    loan_account_id: UUID
    request_type: ServiceRequestType
    subject: str = Field(..., max_length=255)
    description: Optional[str] = None


class ServiceRequestResponse(BaseModel):
    """Service request response."""

    id: str
    request_number: str
    request_type: str
    subject: str
    status: str
    status_message: Optional[str] = None
    created_at: str
    sla_due_at: Optional[str] = None
    is_sla_breached: bool


class ServiceRequestDetails(BaseModel):
    """Detailed service request."""

    id: str
    request_number: str
    request_type: str
    subject: str
    description: Optional[str] = None
    status: str
    status_message: Optional[str] = None
    created_at: str
    sla_due_at: Optional[str] = None
    is_sla_breached: bool
    requested_amount: Optional[float] = None
    quote_amount: Optional[float] = None
    quote_valid_until: Optional[str] = None
    current_emi_date: Optional[int] = None
    requested_emi_date: Optional[int] = None
    documents: List[dict]
    history: List[dict]


class PrepaymentRequest(BaseModel):
    """Prepayment request."""

    loan_account_id: UUID
    prepayment_amount: Decimal = Field(..., gt=0)
    prepayment_date: Optional[date] = None


class ForeclosureRequest(BaseModel):
    """Foreclosure request."""

    loan_account_id: UUID
    foreclosure_date: Optional[date] = None


class EMIDateChangeRequest(BaseModel):
    """EMI date change request."""

    loan_account_id: UUID
    current_emi_date: int = Field(..., ge=1, le=28)
    new_emi_date: int = Field(..., ge=1, le=28)
    effective_from: date
    reason: Optional[str] = None


class FeedbackRequest(BaseModel):
    """Submit feedback request."""

    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Paginated response."""

    items: List
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Service Request CRUD
# =============================================================================


@router.post(
    "",
    response_model=ServiceRequestResponse, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Create Service Request",
)
async def create_request(
    request: ServiceRequestCreate,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Create a new service request."""
    service = PortalServiceRequestService(db)
    sr = await service.create_request(
        organization_id=user.organization_id,
        user_id=user.id,
        **request.model_dump(),
    )
    await db.commit()

    return ServiceRequestResponse(
        id=str(sr.id),
        request_number=sr.request_number,
        request_type=sr.request_type.value,
        subject=sr.subject,
        status=sr.status.value,
        status_message=sr.status_message,
        created_at=sr.created_at.isoformat(),
        sla_due_at=sr.sla_due_at.isoformat() if sr.sla_due_at else None,
        is_sla_breached=sr.is_sla_breached,
    )


@router.get(
    "",
    response_model=PaginatedResponse, response_model_by_alias=True,
    summary="Get Service Requests",
)
async def get_requests(
    loan_account_id: Optional[UUID] = None,
    request_type: Optional[ServiceRequestType] = None,
    status: Optional[ServiceRequestStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Get service requests."""
    service = PortalServiceRequestService(db)
    items, total = await service.get_requests(
        user_id=user.id,
        loan_account_id=loan_account_id,
        request_type=request_type,
        status=status,
        page=page,
        page_size=page_size,
    )

    return PaginatedResponse(
        items=[ServiceRequestResponse(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.get(
    "/{request_id}",
    response_model=ServiceRequestDetails, response_model_by_alias=True,
    summary="Get Service Request Details",
)
async def get_request_details(
    request_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Get detailed service request information."""
    service = PortalServiceRequestService(db)
    details = await service.get_request_details(request_id, user.id)

    if not details:
        raise NotFoundException(
            detail="Service request not found",
            error_code="SERVICE_REQUEST_NOT_FOUND",
        )

    return ServiceRequestDetails(**details)


@router.post(
    "/{request_id}/submit",
    response_model=ServiceRequestResponse, response_model_by_alias=True,
    summary="Submit Service Request",
)
async def submit_request(
    request_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Submit a draft service request."""
    service = PortalServiceRequestService(db)

    try:
        sr = await service.submit_request(request_id, user.id)
        await db.commit()
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    return ServiceRequestResponse(
        id=str(sr.id),
        request_number=sr.request_number,
        request_type=sr.request_type.value,
        subject=sr.subject,
        status=sr.status.value,
        status_message=sr.status_message,
        created_at=sr.created_at.isoformat(),
        sla_due_at=sr.sla_due_at.isoformat() if sr.sla_due_at else None,
        is_sla_breached=sr.is_sla_breached,
    )


@router.delete(
    "/{request_id}",
    summary="Cancel Service Request",
)
async def cancel_request(
    request_id: UUID,
    reason: str = "Customer requested",
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Cancel a service request."""
    service = PortalServiceRequestService(db)
    success = await service.cancel_request(request_id, user.id, reason)
    await db.commit()

    if not success:
        raise NotFoundException(
            detail="Request not found or cannot be cancelled",
            error_code="REQUEST_NOT_FOUND_OR_CANNOT_BE",
        )

    return {"message": "Request cancelled"}


# =============================================================================
# Prepayment
# =============================================================================


@router.post(
    "/prepayment",
    summary="Create Prepayment Request",
)
async def create_prepayment_request(
    request: PrepaymentRequest,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """
    Create a prepayment request with quote.

    Returns the request with calculated prepayment amount and charges.
    """
    service = PortalServiceRequestService(db)
    result = await service.create_prepayment_request(
        organization_id=user.organization_id,
        user_id=user.id,
        loan_account_id=request.loan_account_id,
        prepayment_amount=request.prepayment_amount,
        prepayment_date=request.prepayment_date,
    )
    await db.commit()

    return result


# =============================================================================
# Foreclosure
# =============================================================================


@router.post(
    "/foreclosure",
    summary="Create Foreclosure Request",
)
async def create_foreclosure_request(
    request: ForeclosureRequest,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """
    Create a foreclosure request with quote.

    Returns the request with calculated foreclosure amount including all charges.
    """
    service = PortalServiceRequestService(db)
    result = await service.create_foreclosure_request(
        organization_id=user.organization_id,
        user_id=user.id,
        loan_account_id=request.loan_account_id,
        foreclosure_date=request.foreclosure_date,
    )
    await db.commit()

    return result


# =============================================================================
# EMI Date Change
# =============================================================================


@router.post(
    "/emi-date-change",
    response_model=ServiceRequestResponse, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Request EMI Date Change",
)
async def create_emi_date_change_request(
    request: EMIDateChangeRequest,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """
    Request change in EMI deduction date.

    New date must be between 1-28 of the month.
    """
    service = PortalServiceRequestService(db)

    try:
        sr = await service.create_emi_date_change_request(
            organization_id=user.organization_id,
            user_id=user.id,
            loan_account_id=request.loan_account_id,
            current_emi_date=request.current_emi_date,
            new_emi_date=request.new_emi_date,
            effective_from=request.effective_from,
            reason=request.reason,
        )
        await db.commit()
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    return ServiceRequestResponse(
        id=str(sr.id),
        request_number=sr.request_number,
        request_type=sr.request_type.value,
        subject=sr.subject,
        status=sr.status.value,
        status_message=sr.status_message,
        created_at=sr.created_at.isoformat(),
        sla_due_at=sr.sla_due_at.isoformat() if sr.sla_due_at else None,
        is_sla_breached=sr.is_sla_breached,
    )


# =============================================================================
# Document Upload
# =============================================================================


@router.post(
    "/{request_id}/documents",
    summary="Upload Document",
)
async def upload_document(
    request_id: UUID,
    document_type: str,
    file: UploadFile = File(...),
    description: Optional[str] = None,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """
    Upload a document for a service request.

    Supported file types: PDF, JPG, PNG (max 5MB)
    """
    # Validate file
    max_size = 5 * 1024 * 1024  # 5MB
    content = await file.read()

    if len(content) > max_size:
        raise BadRequestException(
            detail="File size exceeds 5MB limit",
            error_code="FILE_SIZE_EXCEEDS_MB_LIMIT",
        )

    allowed_types = ["application/pdf", "image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise BadRequestException(
            detail="Invalid file type. Allowed: PDF, JPG, PNG",
            error_code="INVALID_FILE_TYPE_ALLOWED_PDF_JPG",
        )

    # Save file (placeholder - would save to S3/storage)
    file_path = f"/uploads/service-requests/{request_id}/{file.filename}"

    service = PortalServiceRequestService(db)

    try:
        document = await service.upload_document(
            request_id=request_id,
            user_id=user.id,
            document_name=file.filename,
            document_type=document_type,
            file_name=file.filename,
            file_type=file.content_type,
            file_size=len(content),
            file_path=file_path,
        )
        await db.commit()
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    return {
        "document_id": str(document.id),
        "document_name": document.document_name,
        "message": "Document uploaded successfully",
    }


# =============================================================================
# Feedback
# =============================================================================


@router.post(
    "/{request_id}/feedback",
    summary="Submit Feedback",
)
async def submit_feedback(
    request_id: UUID,
    feedback: FeedbackRequest,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Submit feedback for a completed service request."""
    service = PortalServiceRequestService(db)

    try:
        success = await service.submit_feedback(
            request_id=request_id,
            user_id=user.id,
            rating=feedback.rating,
            feedback=feedback.feedback,
        )
        await db.commit()
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    if not success:
        raise NotFoundException(
            detail="Request not found or not completed",
            error_code="REQUEST_NOT_FOUND_OR_NOT_COMPLETED",
        )

    return {"message": "Feedback submitted successfully"}
