"""Loan Disbursement API endpoints."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.models.lending.enums import DisbursementStatus
from app.schemas.base import CamelSchema, PaginatedResponse
from app.schemas.lending.loan_account import DisbursementListResponse
from app.services.lending import DisbursementService

router = APIRouter()


# Request/Response Schemas
class DisbursementCreateRequest(CamelSchema):
    """Request to create a disbursement."""

    loan_account_id: UUID
    requested_amount: Decimal = Field(..., gt=0)
    beneficiary_name: str
    beneficiary_account_number: str
    beneficiary_ifsc: str
    disbursement_mode: str = Field(default="RTGS")
    scheduled_date: date | None = None
    purpose: str | None = None
    beneficiary_bank: str | None = None
    bank_account_id: UUID | None = None
    milestone_id: UUID | None = None


class DisbursementResponse(CamelSchema):
    """Disbursement response."""

    id: UUID
    disbursement_reference: str
    loan_account_id: UUID
    disbursement_number: int
    requested_amount: Decimal
    approved_amount: Decimal | None
    disbursed_amount: Decimal | None
    status: str
    disbursement_mode: str
    beneficiary_name: str
    request_date: date
    scheduled_date: date | None
    disbursement_date: date | None
    conditions_verified: bool


class VerifyConditionsRequest(CamelSchema):
    """Request to verify disbursement conditions."""

    disbursement_id: UUID
    verification_notes: str | None = None


class ApprovalRequest(CamelSchema):
    """Request to approve disbursement."""

    disbursement_id: UUID
    approved_amount: Decimal | None = None
    remarks: str | None = None


class ProcessRequest(CamelSchema):
    """Request to process disbursement."""

    disbursement_id: UUID
    disbursed_amount: Decimal = Field(..., gt=0)
    disbursement_date: date | None = None
    value_date: date | None = None
    utr_number: str | None = None
    cheque_number: str | None = None
    disbursement_charges: Decimal = Field(default=Decimal("0"))


class RejectRequest(CamelSchema):
    """Request to reject disbursement."""

    disbursement_id: UUID
    rejection_reason: str


class ReverseRequest(CamelSchema):
    """Request to reverse disbursement."""

    disbursement_id: UUID
    reversal_reason: str
    reversal_date: date | None = None


class TrancheItem(CamelSchema):
    """Single tranche in multi-tranche disbursement."""

    amount: Decimal = Field(..., gt=0)
    beneficiary_name: str
    beneficiary_account: str
    beneficiary_ifsc: str
    mode: str = Field(default="RTGS")
    scheduled_date: date | None = None
    purpose: str | None = None
    beneficiary_bank: str | None = None
    milestone_id: UUID | None = None


class TrancheRequest(CamelSchema):
    """Multi-tranche disbursement request."""

    loan_account_id: UUID
    tranches: list[TrancheItem]


class DisbursementSummaryResponse(CamelSchema):
    """Disbursement summary response."""

    from_date: date
    to_date: date
    disbursed: dict
    by_mode: dict
    pending_count: int
    approved: dict


class DisbursementActionLoanAccount(CamelSchema):
    """Loan balance fields returned after a disbursement action."""

    id: UUID
    total_disbursed: Decimal
    undisbursed: Decimal | None = None
    principal_outstanding: Decimal
    status: str


class DisbursementActionResponse(CamelSchema):
    """Acknowledgement for manual disbursement workflow actions."""

    disbursement_id: UUID
    status: str
    message: str
    approved_amount: Decimal | None = None
    approval_date: date | None = None
    disbursed_amount: Decimal | None = None
    net_disbursement: Decimal | None = None
    utr_number: str | None = None
    loan_account: DisbursementActionLoanAccount | None = None


# Endpoints
@router.get(
    "",
    response_model=PaginatedResponse[DisbursementListResponse],
    response_model_by_alias=True,
)
async def list_disbursements(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: str | None = Query(None),
    status: DisbursementStatus | None = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Paginated list of disbursements scoped to caller's org."""
    service = DisbursementService(db)
    skip = (page - 1) * page_size
    items, total = await service.list_disbursements_for_org(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=page_size,
        search=search,
        status=status,
    )
    list_items = [DisbursementListResponse.model_validate(d) for d in items]
    return PaginatedResponse.create(list_items, total, page, page_size)


@router.post(
    "/",
    response_model=DisbursementResponse,
    response_model_by_alias=True,
)
async def create_disbursement(
    request: DisbursementCreateRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Create a new disbursement request."""
    service = DisbursementService(db)

    disbursement = await service.create_disbursement_request(
        loan_account_id=request.loan_account_id,
        requested_amount=request.requested_amount,
        beneficiary_name=request.beneficiary_name,
        beneficiary_account=request.beneficiary_account_number,
        beneficiary_ifsc=request.beneficiary_ifsc,
        disbursement_mode=request.disbursement_mode,
        scheduled_date=request.scheduled_date,
        purpose=request.purpose,
        beneficiary_bank=request.beneficiary_bank,
        bank_account_id=request.bank_account_id,
        milestone_id=request.milestone_id,
        user_id=current_user.id,
    )

    return DisbursementResponse(
        id=disbursement.id,
        disbursement_reference=disbursement.disbursement_reference,
        loan_account_id=disbursement.loan_account_id,
        disbursement_number=disbursement.disbursement_number,
        requested_amount=disbursement.requested_amount,
        approved_amount=disbursement.approved_amount,
        disbursed_amount=disbursement.disbursed_amount,
        status=disbursement.status.name,
        disbursement_mode=disbursement.disbursement_mode.name,
        beneficiary_name=disbursement.beneficiary_name,
        request_date=disbursement.request_date,
        scheduled_date=disbursement.scheduled_date,
        disbursement_date=disbursement.disbursement_date,
        conditions_verified=disbursement.conditions_verified,
    )


@router.post("/verify-conditions")
async def verify_conditions(
    request: VerifyConditionsRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Verify pre-disbursement conditions."""
    service = DisbursementService(db)

    disbursement = await service.verify_conditions(
        disbursement_id=request.disbursement_id,
        verification_notes=request.verification_notes,
        user_id=current_user.id,
    )

    return {
        "disbursement_id": str(disbursement.id),
        "conditions_verified": disbursement.conditions_verified,
        "verified_at": disbursement.conditions_verified_at,
        "message": "Conditions verified successfully",
    }


@router.post(
    "/approve",
    response_model=DisbursementActionResponse,
    response_model_by_alias=True,
)
async def approve_disbursement(
    request: ApprovalRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Approve a disbursement request."""
    service = DisbursementService(db)

    disbursement = await service.approve_disbursement(
        disbursement_id=request.disbursement_id,
        approved_amount=request.approved_amount,
        remarks=request.remarks,
        user_id=current_user.id,
    )

    return {
        "disbursement_id": disbursement.id,
        "status": disbursement.status.name,
        "approved_amount": disbursement.approved_amount,
        "approval_date": disbursement.approval_date,
        "message": "Disbursement approved successfully",
    }


@router.post(
    "/reject",
    response_model=DisbursementActionResponse,
    response_model_by_alias=True,
)
async def reject_disbursement(
    request: RejectRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Reject a disbursement request."""
    service = DisbursementService(db)

    disbursement = await service.reject_disbursement(
        disbursement_id=request.disbursement_id,
        rejection_reason=request.rejection_reason,
        user_id=current_user.id,
    )

    return {
        "disbursement_id": disbursement.id,
        "status": disbursement.status.name,
        "message": "Disbursement rejected",
    }


@router.post(
    "/process",
    response_model=DisbursementActionResponse,
    response_model_by_alias=True,
)
async def process_disbursement(
    request: ProcessRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Process an approved disbursement."""
    service = DisbursementService(db)

    disbursement, loan = await service.process_disbursement(
        disbursement_id=request.disbursement_id,
        disbursed_amount=request.disbursed_amount,
        disbursement_date=request.disbursement_date,
        value_date=request.value_date,
        utr_number=request.utr_number,
        cheque_number=request.cheque_number,
        disbursement_charges=request.disbursement_charges,
        user_id=current_user.id,
    )

    return {
        "disbursement_id": disbursement.id,
        "status": disbursement.status.name,
        "disbursed_amount": disbursement.disbursed_amount,
        "net_disbursement": disbursement.net_disbursement,
        "utr_number": disbursement.utr_number,
        "loan_account": {
            "id": loan.id,
            "total_disbursed": loan.total_disbursed_amount,
            "undisbursed": loan.undisbursed_amount,
            "principal_outstanding": loan.principal_outstanding,
            "status": loan.status.name,
        },
        "message": "Disbursement processed successfully",
    }


@router.post("/cancel")
async def cancel_disbursement(
    disbursement_id: UUID = Query(..., description="Disbursement ID"),
    cancellation_reason: str = Query(..., description="Reason for cancellation"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Cancel a pending or approved disbursement."""
    service = DisbursementService(db)

    disbursement = await service.cancel_disbursement(
        disbursement_id=disbursement_id,
        cancellation_reason=cancellation_reason,
        user_id=current_user.id,
    )

    return {
        "disbursement_id": str(disbursement.id),
        "status": disbursement.status.name,
        "message": "Disbursement cancelled",
    }


@router.post("/reverse")
async def reverse_disbursement(
    request: ReverseRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Reverse a completed disbursement."""
    service = DisbursementService(db)

    disbursement, loan = await service.reverse_disbursement(
        disbursement_id=request.disbursement_id,
        reversal_reason=request.reversal_reason,
        reversal_date=request.reversal_date,
        user_id=current_user.id,
    )

    return {
        "disbursement_id": str(disbursement.id),
        "status": disbursement.status.name,
        "loan_account": {
            "id": str(loan.id),
            "total_disbursed": loan.total_disbursed_amount,
            "principal_outstanding": loan.principal_outstanding,
            "status": loan.status.name,
        },
        "message": "Disbursement reversed successfully",
    }


@router.post("/tranches")
async def create_tranche_disbursements(
    request: TrancheRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Create multiple tranche disbursements."""
    service = DisbursementService(db)

    tranche_data = [t.dict() for t in request.tranches]

    disbursements = await service.create_tranche_disbursement(
        loan_account_id=request.loan_account_id,
        tranche_data=tranche_data,
        user_id=current_user.id,
    )

    return {
        "loan_account_id": str(request.loan_account_id),
        "tranche_count": len(disbursements),
        "total_amount": sum(d.requested_amount for d in disbursements),
        "disbursements": [
            {
                "id": str(d.id),
                "disbursement_reference": d.disbursement_reference,
                "requested_amount": d.requested_amount,
                "status": d.status.name,
            }
            for d in disbursements
        ],
    }


@router.get("/loan/{loan_account_id}")
async def get_disbursements_by_loan(
    loan_account_id: UUID,
    status: str | None = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Get disbursements for a loan account."""
    service = DisbursementService(db)

    disbursements = await service.get_disbursements(
        loan_account_id=loan_account_id,
        status=status,
    )

    return {
        "loan_account_id": str(loan_account_id),
        "count": len(disbursements),
        "disbursements": [
            {
                "id": str(d.id),
                "disbursement_reference": d.disbursement_reference,
                "disbursement_number": d.disbursement_number,
                "requested_amount": d.requested_amount,
                "approved_amount": d.approved_amount,
                "disbursed_amount": d.disbursed_amount,
                "status": d.status.name,
                "request_date": d.request_date,
                "disbursement_date": d.disbursement_date,
                "utr_number": d.utr_number,
            }
            for d in disbursements
        ],
    }


@router.get("/pending")
async def get_pending_disbursements(
    disb_status: str | None = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get pending disbursements for organization."""
    service = DisbursementService(db)

    disbursements = await service.get_pending_disbursements(
        organization_id=current_user.organization_id,
        status=disb_status,
    )

    return {
        "organization_id": str(current_user.organization_id),
        "count": len(disbursements),
        "disbursements": disbursements,
    }


@router.get(
    "/summary",
    response_model=DisbursementSummaryResponse,
    response_model_by_alias=True,
)
async def get_disbursement_summary(
    from_date: date | None = None,
    to_date: date | None = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get disbursement summary for organization."""
    service = DisbursementService(db)

    summary = await service.get_disbursement_summary(
        organization_id=current_user.organization_id,
        from_date=from_date,
        to_date=to_date,
    )

    return DisbursementSummaryResponse(**summary)
