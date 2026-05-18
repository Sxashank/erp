"""Credit Bureau API endpoints for credit report pulls and analysis."""

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.models.lending.credit_pull import CreditPullStatus
from app.schemas.lending.credit import (
    CreditAccountResponse,
    CreditBureauStats,
    CreditEnquiryResponse,
    CreditPullBulkRequest,
    CreditPullListResponse,
    CreditPullRequest,
    CreditPullResponse,
    CreditPullSummaryResponse,
    CreditReportAnalysis,
    PaginatedCreditPullResponse,
)
from app.services.lending.credit_service import CreditService
from app.core.exceptions import BadRequestException, InternalServerException, NotFoundException

router = APIRouter(prefix="/credit", tags=["Credit Bureau"])


# =============================================================================
# Credit Pull Endpoints
# =============================================================================


@router.post("/pull", response_model=CreditPullResponse, response_model_by_alias=True)
async def initiate_credit_pull(
    request: CreditPullRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Initiate a credit bureau pull.

    Pulls credit report from the specified bureau (CIBIL, Experian, Equifax, CRIF).
    A soft pull won't affect the customer's credit score.
    """
    service = CreditService(db)
    try:
        credit_pull = await service.pull_credit_report(
            organization_id=current_user.organization_id,
            request=request,
            pulled_by_id=current_user.id,
        )

        return _build_credit_pull_response(credit_pull)

    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")
    except Exception as e:
        raise InternalServerException(
            detail=f"Credit pull failed: {str(e)}",
            error_code="CREDIT_PULL_FAILED",
        )


@router.post("/pull/bulk")
async def initiate_bulk_credit_pull(
    request: CreditPullBulkRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Initiate credit pulls from multiple bureaus simultaneously.

    Useful for comparing scores across bureaus or getting comprehensive
    credit view during underwriting.
    """
    service = CreditService(db)
    results = []
    errors = []

    for bureau in request.bureaus:
        try:
            single_request = CreditPullRequest(
                bureau=bureau,
                pull_type=request.pull_type,
                customer_name=request.customer_name,
                pan_number=request.pan_number,
                date_of_birth=request.date_of_birth,
                mobile_number=request.mobile_number,
                entity_id=request.entity_id,
                loan_application_id=request.loan_application_id,
            )

            credit_pull = await service.pull_credit_report(
                organization_id=current_user.organization_id,
                request=single_request,
                pulled_by_id=current_user.id,
            )
            results.append(
                {
                    "bureau": bureau,
                    "success": True,
                    "pull_id": str(credit_pull.id),
                    "credit_score": credit_pull.credit_score,
                    "status": credit_pull.status.value,
                }
            )
        except Exception as e:
            errors.append(
                {
                    "bureau": bureau,
                    "success": False,
                    "error": str(e),
                }
            )

    return {
        "total_requested": len(request.bureaus),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }


@router.get("/pulls", response_model=PaginatedCreditPullResponse, response_model_by_alias=True)
async def list_credit_pulls(
    entity_id: UUID | None = None,
    loan_application_id: UUID | None = None,
    bureau: str | None = None,
    pull_status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List credit pulls with filtering and pagination."""
    service = CreditService(db)

    # Convert status string to enum if provided
    status_enum = None
    if pull_status:
        try:
            status_enum = CreditPullStatus(pull_status)
        except ValueError:
            raise BadRequestException(
                detail=f"Invalid status: {pull_status}",
                error_code="INVALID_STATUS",
            )

    result = await service.list_credit_pulls(
        organization_id=current_user.organization_id,
        entity_id=entity_id,
        loan_application_id=loan_application_id,
        bureau=bureau,
        status=status_enum.value if status_enum else None,
        page=page,
        page_size=page_size,
    )
    pulls = result["items"]
    total = result["total"]

    items = []
    for pull in pulls:
        items.append(
            CreditPullListResponse(
                id=pull.id,
                organization_id=pull.organization_id,
                entity_id=pull.entity_id,
                loan_application_id=pull.loan_application_id,
                bureau=pull.bureau.value,
                pull_type=pull.pull_type.value,
                status=pull.status.value,
                customer_name=pull.customer_name,
                pan_number=pull.pan_number,
                credit_score=pull.credit_score,
                score_band=pull.score_band,
                pulled_at=pull.pulled_at,
                expires_at=pull.expires_at,
                is_valid=_is_pull_valid(pull),
                created_at=pull.created_at,
            )
        )

    return PaginatedCreditPullResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/pulls/{pull_id}", response_model=CreditPullResponse, response_model_by_alias=True)
async def get_credit_pull(
    pull_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get credit pull details with full report data."""
    service = CreditService(db)
    pull = await service.get_credit_pull(pull_id)

    if not pull:
        raise NotFoundException(detail="Credit pull not found", error_code="CREDIT_PULL_NOT_FOUND")

    return _build_credit_pull_response(pull)


@router.get(
    "/pulls/{pull_id}/analyze", response_model=CreditReportAnalysis, response_model_by_alias=True
)
async def analyze_credit_report(
    pull_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Analyze credit report with detailed breakdown.

    Returns comprehensive analysis including:
    - Score band and percentile
    - Account summary by type
    - DPD analysis
    - Enquiry analysis
    - Risk indicators
    """
    service = CreditService(db)
    pull = await service.get_credit_pull(pull_id)

    if not pull:
        raise NotFoundException(detail="Credit pull not found", error_code="CREDIT_PULL_NOT_FOUND")

    if pull.status != CreditPullStatus.SUCCESS:
        raise BadRequestException(
            detail="Cannot analyze failed or pending credit pull",
            error_code="CANNOT_ANALYZE_FAILED_OR_PENDING_CREDIT",
        )

    analysis = await service.analyze_report(pull_id)
    return analysis


# =============================================================================
# Summary & Lookup Endpoints
# =============================================================================


@router.get("/summary", response_model=CreditPullSummaryResponse, response_model_by_alias=True)
async def get_credit_summary(
    entity_id: UUID | None = None,
    loan_application_id: UUID | None = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get credit summary for an entity or loan application.

    Returns latest scores and pull history summary.
    """
    if not entity_id and not loan_application_id:
        raise BadRequestException(
            detail="Either entity_id or loan_application_id is required",
            error_code="EITHER_ENTITY_ID_OR_LOAN_APPLICATION_ID_IS_REQUIRED",
        )

    service = CreditService(db)
    summary = await service.get_credit_summary(
        organization_id=current_user.organization_id,
        entity_id=entity_id,
        loan_application_id=loan_application_id,
    )

    return summary


@router.get("/latest-score")
async def get_latest_credit_score(
    entity_id: UUID | None = None,
    pan_number: str | None = None,
    bureau: str | None = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get latest credit score for a customer.

    Looks up by entity_id or PAN number. Returns cached score if valid,
    otherwise indicates a new pull is needed.
    """
    if not entity_id and not pan_number:
        raise BadRequestException(
            detail="Either entity_id or pan_number is required",
            error_code="EITHER_ENTITY_ID_OR_PAN_NUMBER_IS_REQUIRED",
        )

    service = CreditService(db)
    result = await service.get_latest_score(
        organization_id=current_user.organization_id,
        entity_id=entity_id,
        pan_number=pan_number,
        bureau=bureau,
    )

    if result:
        return {
            "found": True,
            "credit_score": result.get("credit_score"),
            "score_band": result.get("score_band"),
            "bureau": result.get("bureau"),
            "pulled_at": result.get("pulled_at"),
            "expires_at": result.get("expires_at"),
            "is_valid": result.get("is_valid", False),
            "pull_id": result.get("pull_id"),
        }
    else:
        return {
            "found": False,
            "message": "No valid credit score found. Please initiate a new pull.",
        }


# =============================================================================
# Statistics & Reporting
# =============================================================================


@router.get("/statistics", response_model=CreditBureauStats, response_model_by_alias=True)
async def get_credit_bureau_statistics(
    start_date: date | None = None,
    end_date: date | None = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get credit bureau usage statistics.

    Returns metrics on bureau pulls, success rates, and score distribution.
    """
    service = CreditService(db)
    stats = await service.get_statistics(
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
    )

    return stats


@router.get("/score-bands")
async def get_score_band_definitions():
    """Get credit score band definitions.

    Returns the score ranges and their classifications.
    """
    return {
        "bands": [
            {
                "band": "EXCELLENT",
                "min_score": 750,
                "max_score": 900,
                "description": "Excellent credit",
            },
            {"band": "GOOD", "min_score": 700, "max_score": 749, "description": "Good credit"},
            {"band": "FAIR", "min_score": 650, "max_score": 699, "description": "Fair credit"},
            {"band": "POOR", "min_score": 550, "max_score": 649, "description": "Poor credit"},
            {
                "band": "VERY_POOR",
                "min_score": 300,
                "max_score": 549,
                "description": "Very poor credit",
            },
        ],
        "note": "Score bands may vary slightly between bureaus",
    }


# =============================================================================
# Helper Functions
# =============================================================================


def _build_credit_pull_response(pull) -> CreditPullResponse:
    """Build CreditPullResponse from model."""
    accounts = []
    for acc in pull.accounts:
        accounts.append(
            CreditAccountResponse(
                id=acc.id,
                account_number_masked=acc.account_number_masked,
                institution_name=acc.institution_name,
                institution_type=acc.institution_type,
                account_type=(
                    acc.account_type.value
                    if hasattr(acc.account_type, "value")
                    else acc.account_type
                ),
                account_status=(
                    acc.account_status.value
                    if hasattr(acc.account_status, "value")
                    else acc.account_status
                ),
                ownership=acc.ownership.value if hasattr(acc.ownership, "value") else acc.ownership,
                sanctioned_amount=acc.sanctioned_amount,
                current_balance=acc.current_balance,
                overdue_amount=acc.overdue_amount,
                emi_amount=acc.emi_amount,
                credit_limit=acc.credit_limit,
                high_credit=acc.high_credit,
                write_off_amount=acc.write_off_amount,
                opened_date=acc.opened_date,
                closed_date=acc.closed_date,
                last_payment_date=acc.last_payment_date,
                reported_date=acc.reported_date,
                tenure_months=acc.tenure_months,
                remaining_tenure=acc.remaining_tenure,
                max_dpd=acc.max_dpd,
                dpd_history=acc.dpd_history,
                is_secured=acc.is_secured,
                has_dispute=acc.has_dispute,
            )
        )

    enquiries = []
    for enq in pull.enquiries:
        enquiries.append(
            CreditEnquiryResponse(
                id=enq.id,
                enquiry_date=enq.enquiry_date,
                institution_name=enq.institution_name,
                enquiry_purpose=enq.enquiry_purpose,
                enquiry_amount=enq.enquiry_amount,
            )
        )

    return CreditPullResponse(
        id=pull.id,
        organization_id=pull.organization_id,
        entity_id=pull.entity_id,
        loan_application_id=pull.loan_application_id,
        bureau=pull.bureau.value,
        pull_type=pull.pull_type.value,
        status=pull.status.value,
        customer_name=pull.customer_name,
        pan_number=pull.pan_number,
        request_reference=pull.request_reference,
        bureau_reference=pull.bureau_reference,
        credit_score=pull.credit_score,
        score_version=pull.score_version,
        score_date=pull.score_date,
        score_band=pull.score_band,
        total_accounts=pull.total_accounts,
        active_accounts=pull.active_accounts,
        total_sanctioned=pull.total_sanctioned,
        total_outstanding=pull.total_outstanding,
        total_overdue=pull.total_overdue,
        max_dpd_last_12m=pull.max_dpd_last_12m,
        max_dpd_last_24m=pull.max_dpd_last_24m,
        enquiries_last_30d=pull.enquiries_last_30d,
        enquiries_last_12m=pull.enquiries_last_12m,
        error_code=pull.error_code,
        error_message=pull.error_message,
        pulled_at=pull.pulled_at,
        expires_at=pull.expires_at,
        created_at=pull.created_at,
        accounts=accounts,
        enquiries=enquiries,
        is_valid=_is_pull_valid(pull),
    )


def _is_pull_valid(pull) -> bool:
    """Check if credit pull is still valid."""
    if pull.status != CreditPullStatus.SUCCESS:
        return False
    if not pull.expires_at:
        return False
    return datetime.utcnow() < pull.expires_at
