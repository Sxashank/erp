"""Repayment matching endpoints for imported bank-statement credits."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.lending.repayment_matching import (
    CreateMatchedReceiptRequest,
    CreateMatchedReceiptResponse,
    RepaymentMatchingResponse,
    RepaymentMatchingSummary,
)
from app.services.lending.repayment_matching_service import RepaymentMatchingService
from app.core.exceptions import BadRequestException

router = APIRouter()


@router.get(
    "/summary",
    response_model=RepaymentMatchingSummary,
    response_model_by_alias=True,
)
async def get_repayment_matching_summary(
    bank_account_id: UUID | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> RepaymentMatchingSummary:
    service = RepaymentMatchingService(db)
    return await service.get_summary(
        organization_id=current_user.organization_id,
        bank_account_id=bank_account_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get(
    "/candidates",
    response_model=RepaymentMatchingResponse,
    response_model_by_alias=True,
)
async def list_repayment_match_candidates(
    bank_account_id: UUID | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    min_confidence: Decimal = Query(Decimal("0"), ge=0, le=100),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> RepaymentMatchingResponse:
    service = RepaymentMatchingService(db)
    return await service.get_candidates(
        organization_id=current_user.organization_id,
        bank_account_id=bank_account_id,
        from_date=from_date,
        to_date=to_date,
        min_confidence=min_confidence,
        limit=limit,
    )


@router.post(
    "/statements/{statement_id}/create-receipt",
    response_model=CreateMatchedReceiptResponse,
    response_model_by_alias=True,
)
async def create_receipt_from_statement(
    statement_id: UUID,
    request: CreateMatchedReceiptRequest,
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> CreateMatchedReceiptResponse:
    service = RepaymentMatchingService(db)
    try:
        return await service.create_receipt_from_statement(
            organization_id=current_user.organization_id,
            statement_id=statement_id,
            loan_account_id=request.loan_account_id,
            auto_allocate=request.auto_allocate,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise BadRequestException(detail=str(exc), error_code="BAD_REQUEST") from exc
