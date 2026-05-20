"""Portal Payment API endpoints."""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, status, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.v1.portal.auth import get_portal_db_with_tenant, get_portal_user
from app.models.portal.enums import PaymentMode, MandateFrequency
from app.services.portal.payment_service import PortalPaymentService
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter(prefix="/payments", tags=["Portal Payments"])


# =============================================================================
# Request/Response Schemas
# =============================================================================


class PaymentInitiateRequest(BaseModel):
    """Initiate payment request."""

    loan_account_id: UUID
    amount: Decimal = Field(..., gt=0)
    request_type: str = Field(
        ..., description="EMI, PREPAYMENT, FORECLOSURE, CHARGES"
    )
    payment_mode: Optional[PaymentMode] = None
    saved_method_id: Optional[UUID] = None
    gateway: str = "RAZORPAY"


class PaymentInitiateResponse(BaseModel):
    """Payment initiation response."""

    request_id: str
    request_number: str
    amount: float
    gateway: str
    order_id: str
    checkout_url: Optional[str] = None
    checkout_data: Optional[dict] = None
    valid_until: str


class PaymentStatusResponse(BaseModel):
    """Payment status response."""

    request_id: str
    request_number: str
    amount: float
    status: str
    status_message: Optional[str] = None
    initiated_at: str
    completed_at: Optional[str] = None
    transaction: Optional[dict] = None


class PaymentHistoryItem(BaseModel):
    """Payment history item."""

    transaction_id: str
    transaction_date: str
    amount: float
    payment_mode: str
    status: str
    gateway_txn_id: Optional[str] = None
    bank_name: Optional[str] = None


class SavedPaymentMethod(BaseModel):
    """Saved payment method."""

    id: str
    method_type: str
    display_name: str
    is_default: bool
    card_last4: Optional[str] = None
    card_network: Optional[str] = None
    upi_vpa: Optional[str] = None
    bank_name: Optional[str] = None
    last_used_at: Optional[str] = None


class SavePaymentMethodRequest(BaseModel):
    """Save payment method request."""

    method_type: str = Field(..., description="CARD, UPI, NETBANKING")
    gateway_name: str = "RAZORPAY"
    card_token: Optional[str] = None
    card_last4: Optional[str] = None
    card_network: Optional[str] = None
    card_type: Optional[str] = None
    upi_vpa: Optional[str] = None
    display_name: Optional[str] = None
    set_as_default: bool = False


class MandateSetupRequest(BaseModel):
    """Setup mandate request."""

    loan_account_id: UUID
    mandate_type: str = Field(..., description="NACH, UPI_AUTOPAY")
    max_amount: Decimal
    frequency: MandateFrequency = MandateFrequency.MONTHLY
    debit_day: int = Field(..., ge=1, le=28)
    start_date: date
    end_date: date
    bank_account_number: Optional[str] = None
    bank_ifsc: Optional[str] = None
    account_holder_name: Optional[str] = None
    upi_vpa: Optional[str] = None


class MandateResponse(BaseModel):
    """Mandate response."""

    mandate_id: str
    internal_mandate_id: str
    status: str
    registration_url: Optional[str] = None
    registration_data: Optional[dict] = None


class MandateStatusResponse(BaseModel):
    """Mandate status response."""

    mandate_id: str
    internal_mandate_id: str
    mandate_type: str
    status: str
    max_amount: float
    frequency: str
    debit_day: int
    start_date: str
    end_date: str
    bank_name: Optional[str] = None
    umrn: Optional[str] = None
    last_execution: Optional[dict] = None


class PaginatedResponse(BaseModel):
    """Paginated response."""

    items: List
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Payment Initiation
# =============================================================================


@router.post(
    "/initiate",
    response_model=PaymentInitiateResponse, response_model_by_alias=True,
    summary="Initiate Payment",
)
async def initiate_payment(
    request: PaymentInitiateRequest,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """
    Initiate a payment.

    Returns checkout data for the selected payment gateway.
    """
    service = PortalPaymentService(db)

    try:
        result = await service.initiate_payment(
            organization_id=user.organization_id,
            user_id=user.id,
            loan_account_id=request.loan_account_id,
            amount=request.amount,
            request_type=request.request_type,
            payment_mode=request.payment_mode,
            saved_method_id=request.saved_method_id,
            gateway_name=request.gateway,
        )
        await db.commit()
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    return PaymentInitiateResponse(**result)


@router.post(
    "/callback/{gateway}",
    summary="Payment Gateway Callback",
)
async def payment_callback(
    gateway: str,
    request: Request,
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """
    Handle payment gateway callback.

    This endpoint is called by the payment gateway after payment completion.
    """
    # Parse callback data based on gateway
    if gateway.upper() == "RAZORPAY":
        callback_data = dict(await request.form())
    else:
        callback_data = await request.json()

    service = PortalPaymentService(db)
    result = await service.process_gateway_callback(
        gateway_name=gateway.upper(),
        callback_data=callback_data,
    )
    await db.commit()

    return result


@router.get(
    "/{request_id}/status",
    response_model=PaymentStatusResponse, response_model_by_alias=True,
    summary="Get Payment Status",
)
async def get_payment_status(
    request_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Get payment request status."""
    service = PortalPaymentService(db)
    result = await service.get_payment_status(request_id, user.id)

    if not result:
        raise NotFoundException(
            detail="Payment request not found",
            error_code="PAYMENT_REQUEST_NOT_FOUND",
        )

    return PaymentStatusResponse(**result)


# =============================================================================
# Payment History
# =============================================================================


@router.get(
    "/history",
    response_model=PaginatedResponse, response_model_by_alias=True,
    summary="Get Payment History",
)
async def get_payment_history(
    loan_account_id: Optional[UUID] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Get payment transaction history."""
    service = PortalPaymentService(db)
    items, total = await service.get_payment_history(
        user_id=user.id,
        loan_account_id=loan_account_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )

    return PaginatedResponse(
        items=[PaymentHistoryItem(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


# =============================================================================
# Saved Payment Methods
# =============================================================================


@router.get(
    "/methods",
    response_model=List[SavedPaymentMethod], response_model_by_alias=True,
    summary="Get Saved Payment Methods",
)
async def get_saved_methods(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Get saved payment methods."""
    service = PortalPaymentService(db)
    methods = await service.get_saved_methods(user.id)

    return [SavedPaymentMethod(**m) for m in methods]


@router.post(
    "/methods",
    response_model=SavedPaymentMethod, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Save Payment Method",
)
async def save_payment_method(
    request: SavePaymentMethodRequest,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Save a payment method for quick payments."""
    service = PortalPaymentService(db)
    method = await service.save_payment_method(
        user_id=user.id,
        **request.model_dump(),
    )
    await db.commit()

    return SavedPaymentMethod(
        id=str(method.id),
        method_type=method.method_type,
        display_name=method.display_name,
        is_default=method.is_default,
        card_last4=method.card_last4,
        card_network=method.card_network,
        upi_vpa=method.upi_vpa,
        bank_name=method.bank_name,
        last_used_at=None,
    )


@router.delete(
    "/methods/{method_id}",
    summary="Delete Saved Payment Method",
)
async def delete_saved_method(
    method_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Delete a saved payment method."""
    service = PortalPaymentService(db)
    success = await service.delete_saved_method(method_id, user.id)
    await db.commit()

    if not success:
        raise NotFoundException(detail="Payment method not found", error_code="PAYMENT_METHOD_NOT_FOUND")

    return {"message": "Payment method deleted"}


# =============================================================================
# Auto-Debit Mandates
# =============================================================================


@router.post(
    "/mandate/setup",
    response_model=MandateResponse, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Setup Auto-Debit Mandate",
)
async def setup_mandate(
    request: MandateSetupRequest,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """
    Setup NACH or UPI Autopay mandate.

    For NACH: Provide bank account details
    For UPI Autopay: Provide UPI VPA
    """
    service = PortalPaymentService(db)
    result = await service.setup_mandate(
        organization_id=user.organization_id,
        user_id=user.id,
        **request.model_dump(),
    )
    await db.commit()

    return MandateResponse(**result)


@router.get(
    "/mandates",
    response_model=List[dict], response_model_by_alias=True,
    summary="Get Mandates",
)
async def get_mandates(
    loan_account_id: Optional[UUID] = None,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Get all mandates for the user."""
    service = PortalPaymentService(db)
    mandates = await service.get_user_mandates(
        user_id=user.id,
        loan_account_id=loan_account_id,
    )

    return mandates


@router.get(
    "/mandates/{mandate_id}",
    response_model=MandateStatusResponse, response_model_by_alias=True,
    summary="Get Mandate Status",
)
async def get_mandate_status(
    mandate_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Get mandate status and details."""
    service = PortalPaymentService(db)
    result = await service.get_mandate_status(mandate_id, user.id)

    if not result:
        raise NotFoundException(detail="Mandate not found", error_code="MANDATE_NOT_FOUND")

    return MandateStatusResponse(**result)


@router.delete(
    "/mandates/{mandate_id}",
    summary="Cancel Mandate",
)
async def cancel_mandate(
    mandate_id: UUID,
    reason: str = "Customer requested",
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
):
    """Cancel an active mandate."""
    service = PortalPaymentService(db)
    success = await service.cancel_mandate(mandate_id, user.id, reason)
    await db.commit()

    if not success:
        raise NotFoundException(
            detail="Mandate not found or cannot be cancelled",
            error_code="MANDATE_NOT_FOUND_OR_CANNOT_BE",
        )

    return {"message": "Mandate cancelled"}
