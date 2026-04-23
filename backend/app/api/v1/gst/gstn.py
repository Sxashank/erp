"""GSTN Portal API endpoints.

Provides endpoints for GST return filing operations:
- Session management (OTP authentication)
- GSTR-1 generation and filing
- GSTR-3B generation and filing
- GSTR-2B fetch
- ITC reconciliation
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, RequirePermissions
from app.models.auth.user import User
from app.models.gst.gstn_models import (
    GSTReturnType,
    GSTReturnStatus,
    ITCMismatchType,
    ITCMismatchResolution,
)
from app.services.gst.gstn_service import GSTNService
from app.schemas.gst.gstn import (
    GSTNOTPRequest,
    GSTNOTPVerify,
    GSTNSessionResponse,
    GSTReturnFilingResponse,
    GSTReturnFilingDetail,
    GSTReturnFilingListResponse,
    GenerateGSTR1Request,
    GenerateGSTR3BRequest,
    FetchGSTR2BRequest,
    RunITCReconciliationRequest,
    ITCMismatchResponse,
    ITCMismatchListResponse,
    ITCMismatchResolve,
    ITCReconciliationSummary,
    GSTR2BListResponse,
    GSTR2BSummary,
)

router = APIRouter(prefix="/gstn", tags=["GSTN Portal"])


# =============================================================================
# Session Management
# =============================================================================

@router.post(
    "/sessions/request-otp",
    summary="Request OTP for GSTN authentication",
    description="Initiate OTP-based authentication with GSTN portal.",
)
async def request_otp(
    organization_id: UUID,
    gst_registration_id: UUID,
    request: GSTNOTPRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.session.create")),
):
    """Request OTP for GSTN authentication."""
    service = GSTNService(db)
    try:
        result = await service.request_otp(
            organization_id=organization_id,
            gst_registration_id=gst_registration_id,
            username=request.username,
            initiated_by=current_user.id,
        )
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "OTP request failed"),
            )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/sessions/{session_id}/verify-otp",
    summary="Verify OTP and establish session",
    description="Verify OTP and get authenticated GSTN session.",
)
async def verify_otp(
    session_id: UUID,
    request: GSTNOTPVerify,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.session.create")),
):
    """Verify OTP and establish GSTN session."""
    service = GSTNService(db)
    try:
        result = await service.verify_otp(
            session_id=session_id,
            username=request.gstin,  # In real impl, this would be stored
            otp=request.otp,
            app_key=request.otp_reference,
        )
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.get("message", "OTP verification failed"),
            )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/sessions/active",
    response_model=Optional[GSTNSessionResponse],
    summary="Get active GSTN session",
    description="Get currently active GSTN session for a GSTIN.",
)
async def get_active_session(
    organization_id: UUID,
    gstin: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.session.read")),
):
    """Get active GSTN session."""
    service = GSTNService(db)
    session = await service.get_active_session(organization_id, gstin)
    if session:
        return GSTNSessionResponse.model_validate(session)
    return None


# =============================================================================
# Return Filing
# =============================================================================

@router.get(
    "/returns",
    response_model=GSTReturnFilingListResponse,
    summary="List GST returns",
    description="List GST return filings with filtering.",
)
async def list_returns(
    organization_id: UUID,
    gst_registration_id: Optional[UUID] = None,
    return_type: Optional[GSTReturnType] = None,
    financial_year: Optional[str] = None,
    return_status: Optional[GSTReturnStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.return.read")),
):
    """List GST return filings."""
    service = GSTNService(db)
    return await service.list_returns(
        organization_id=organization_id,
        gst_registration_id=gst_registration_id,
        return_type=return_type,
        financial_year=financial_year,
        status=return_status,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/returns/{return_id}",
    response_model=GSTReturnFilingDetail,
    summary="Get return details",
    description="Get detailed GST return filing information.",
)
async def get_return(
    return_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.return.read")),
):
    """Get GST return details."""
    from app.models.gst.gstn_models import GSTReturnFiling
    filing = await db.get(GSTReturnFiling, return_id)
    if not filing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Return not found",
        )
    return GSTReturnFilingDetail.model_validate(filing)


# =============================================================================
# GSTR-1
# =============================================================================

@router.post(
    "/gstr1/generate",
    response_model=GSTReturnFilingResponse,
    summary="Generate GSTR-1",
    description="Generate GSTR-1 from sales invoices for a return period.",
)
async def generate_gstr1(
    request: GenerateGSTR1Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.return.create")),
):
    """Generate GSTR-1 from sales data."""
    service = GSTNService(db)
    try:
        gst_reg = await db.get(
            __import__('app.models.gst.gst_registration', fromlist=['GSTRegistration']).GSTRegistration,
            request.gst_registration_id
        )
        if not gst_reg:
            raise ValueError("GST registration not found")

        filing = await service.generate_gstr1(
            organization_id=gst_reg.organization_id,
            gst_registration_id=request.gst_registration_id,
            return_period=request.return_period,
            financial_year=request.financial_year,
            prepared_by=current_user.id,
        )
        return GSTReturnFilingResponse.model_validate(filing)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/gstr1/{return_id}/validate",
    response_model=GSTReturnFilingResponse,
    summary="Validate GSTR-1",
    description="Validate GSTR-1 data with GSTN.",
)
async def validate_gstr1(
    return_id: UUID,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.return.submit")),
):
    """Validate GSTR-1 with GSTN."""
    service = GSTNService(db)
    try:
        filing = await service.validate_gstr1(
            return_id=return_id,
            session_id=session_id,
            validated_by=current_user.id,
        )
        return GSTReturnFilingResponse.model_validate(filing)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/gstr1/{return_id}/submit",
    response_model=GSTReturnFilingResponse,
    summary="Submit GSTR-1",
    description="Submit GSTR-1 to GSTN for filing.",
)
async def submit_gstr1(
    return_id: UUID,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.return.submit")),
):
    """Submit GSTR-1 to GSTN."""
    service = GSTNService(db)
    try:
        filing = await service.submit_gstr1(
            return_id=return_id,
            session_id=session_id,
            submitted_by=current_user.id,
        )
        return GSTReturnFilingResponse.model_validate(filing)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/gstr1/{return_id}/file",
    response_model=GSTReturnFilingResponse,
    summary="File GSTR-1",
    description="File GSTR-1 with EVC/DSC.",
)
async def file_gstr1(
    return_id: UUID,
    session_id: UUID,
    pan: str,
    otp: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.return.file")),
):
    """File GSTR-1 with GSTN."""
    if not otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP is required for filing with EVC",
        )

    service = GSTNService(db)
    try:
        filing = await service.file_gstr1(
            return_id=return_id,
            session_id=session_id,
            pan=pan,
            otp=otp,
            filed_by=current_user.id,
        )
        return GSTReturnFilingResponse.model_validate(filing)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# GSTR-3B
# =============================================================================

@router.post(
    "/gstr3b/generate",
    response_model=GSTReturnFilingResponse,
    summary="Generate GSTR-3B",
    description="Generate GSTR-3B summary for a return period.",
)
async def generate_gstr3b(
    request: GenerateGSTR3BRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.return.create")),
):
    """Generate GSTR-3B summary."""
    service = GSTNService(db)
    try:
        gst_reg = await db.get(
            __import__('app.models.gst.gst_registration', fromlist=['GSTRegistration']).GSTRegistration,
            request.gst_registration_id
        )
        if not gst_reg:
            raise ValueError("GST registration not found")

        filing = await service.generate_gstr3b(
            organization_id=gst_reg.organization_id,
            gst_registration_id=request.gst_registration_id,
            return_period=request.return_period,
            financial_year=request.financial_year,
            prepared_by=current_user.id,
        )
        return GSTReturnFilingResponse.model_validate(filing)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/gstr3b/{return_id}/validate",
    response_model=GSTReturnFilingResponse,
    summary="Validate GSTR-3B",
    description="Validate GSTR-3B data with GSTN.",
)
async def validate_gstr3b(
    return_id: UUID,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.return.submit")),
):
    """Validate GSTR-3B with GSTN."""
    service = GSTNService(db)
    try:
        filing = await service.validate_gstr3b(
            return_id=return_id,
            session_id=session_id,
            validated_by=current_user.id,
        )
        return GSTReturnFilingResponse.model_validate(filing)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/gstr3b/{return_id}/submit",
    response_model=GSTReturnFilingResponse,
    summary="Submit GSTR-3B",
    description="Submit GSTR-3B to GSTN.",
)
async def submit_gstr3b(
    return_id: UUID,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.return.submit")),
):
    """Submit GSTR-3B to GSTN."""
    service = GSTNService(db)
    try:
        filing = await service.submit_gstr3b(
            return_id=return_id,
            session_id=session_id,
            submitted_by=current_user.id,
        )
        return GSTReturnFilingResponse.model_validate(filing)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/gstr3b/{return_id}/file",
    response_model=GSTReturnFilingResponse,
    summary="File GSTR-3B",
    description="File GSTR-3B with EVC/DSC.",
)
async def file_gstr3b(
    return_id: UUID,
    session_id: UUID,
    pan: str,
    otp: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.return.file")),
):
    """File GSTR-3B with GSTN."""
    if not otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP is required for filing with EVC",
        )

    service = GSTNService(db)
    try:
        filing = await service.file_gstr3b(
            return_id=return_id,
            session_id=session_id,
            pan=pan,
            otp=otp,
            filed_by=current_user.id,
        )
        return GSTReturnFilingResponse.model_validate(filing)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# Filing Utilities
# =============================================================================

@router.post(
    "/returns/request-filing-otp",
    summary="Request Filing OTP",
    description="Request OTP for filing return with EVC.",
)
async def request_filing_otp(
    session_id: UUID,
    pan: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.return.file")),
):
    """Request OTP for filing return with EVC."""
    service = GSTNService(db)
    try:
        result = await service.request_filing_otp(
            session_id=session_id,
            pan=pan,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/returns/{return_id}/gstn-status",
    summary="Get Return Status from GSTN",
    description="Get return filing status directly from GSTN portal.",
)
async def get_return_status_from_gstn(
    return_id: UUID,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.return.read")),
):
    """Get return filing status from GSTN."""
    service = GSTNService(db)
    try:
        return await service.get_return_status_from_gstn(
            return_id=return_id,
            session_id=session_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# GSTR-2B and ITC Reconciliation
# =============================================================================

@router.post(
    "/gstr2b/fetch",
    summary="Fetch GSTR-2B from GSTN",
    description="Fetch GSTR-2B data from GSTN portal.",
)
async def fetch_gstr2b(
    request: FetchGSTR2BRequest,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.gstr2b.fetch")),
):
    """Fetch GSTR-2B from GSTN."""
    service = GSTNService(db)
    try:
        gst_reg = await db.get(
            __import__('app.models.gst.gst_registration', fromlist=['GSTRegistration']).GSTRegistration,
            request.gst_registration_id
        )
        if not gst_reg:
            raise ValueError("GST registration not found")

        result = await service.fetch_gstr2b(
            organization_id=gst_reg.organization_id,
            gst_registration_id=request.gst_registration_id,
            return_period=request.return_period,
            session_id=session_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/gstr2b",
    response_model=GSTR2BListResponse,
    summary="List GSTR-2B invoices",
    description="List fetched GSTR-2B invoice data.",
)
async def list_gstr2b(
    organization_id: UUID,
    gst_registration_id: UUID,
    return_period: str,
    supplier_gstin: Optional[str] = None,
    is_matched: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.gstr2b.read")),
):
    """List GSTR-2B invoices."""
    from sqlalchemy import select, and_, func
    from app.models.gst.gstn_models import GSTR2BData

    query = select(GSTR2BData).where(
        and_(
            GSTR2BData.organization_id == organization_id,
            GSTR2BData.gst_registration_id == gst_registration_id,
            GSTR2BData.return_period == return_period,
        )
    )

    if supplier_gstin:
        query = query.where(GSTR2BData.supplier_gstin == supplier_gstin)
    if is_matched is not None:
        query = query.where(GSTR2BData.is_matched == is_matched)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(GSTR2BData.invoice_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    from app.schemas.gst.gstn import GSTR2BInvoiceResponse
    return GSTR2BListResponse(
        items=[GSTR2BInvoiceResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post(
    "/itc-reconciliation/run",
    response_model=ITCReconciliationSummary,
    summary="Run ITC reconciliation",
    description="Run ITC reconciliation between books and GSTR-2B.",
)
async def run_itc_reconciliation(
    request: RunITCReconciliationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.itc.reconcile")),
):
    """Run ITC reconciliation."""
    service = GSTNService(db)
    try:
        gst_reg = await db.get(
            __import__('app.models.gst.gst_registration', fromlist=['GSTRegistration']).GSTRegistration,
            request.gst_registration_id
        )
        if not gst_reg:
            raise ValueError("GST registration not found")

        return await service.run_itc_reconciliation(
            organization_id=gst_reg.organization_id,
            gst_registration_id=request.gst_registration_id,
            return_period=request.return_period,
            auto_match_threshold=request.auto_match_threshold,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/itc-mismatches",
    response_model=ITCMismatchListResponse,
    summary="List ITC mismatches",
    description="List ITC mismatches from reconciliation.",
)
async def list_itc_mismatches(
    organization_id: UUID,
    gst_registration_id: Optional[UUID] = None,
    return_period: Optional[str] = None,
    mismatch_type: Optional[ITCMismatchType] = None,
    resolution_status: Optional[ITCMismatchResolution] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.itc.read")),
):
    """List ITC mismatches."""
    service = GSTNService(db)
    return await service.list_itc_mismatches(
        organization_id=organization_id,
        gst_registration_id=gst_registration_id,
        return_period=return_period,
        mismatch_type=mismatch_type,
        resolution_status=resolution_status,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/itc-mismatches/{mismatch_id}/resolve",
    response_model=ITCMismatchResponse,
    summary="Resolve ITC mismatch",
    description="Resolve an ITC mismatch with resolution status and notes.",
)
async def resolve_itc_mismatch(
    mismatch_id: UUID,
    request: ITCMismatchResolve,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.itc.resolve")),
):
    """Resolve ITC mismatch."""
    service = GSTNService(db)
    try:
        mismatch = await service.resolve_mismatch(
            mismatch_id=mismatch_id,
            resolution_status=request.resolution_status,
            resolution_notes=request.resolution_notes,
            resolved_by=current_user.id,
        )
        return ITCMismatchResponse.model_validate(mismatch)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# Statistics
# =============================================================================

@router.get(
    "/statistics/filings",
    summary="Get filing statistics",
    description="Get GST filing statistics for organization.",
)
async def get_filing_statistics(
    organization_id: UUID,
    financial_year: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.statistics.read")),
):
    """Get filing statistics."""
    from sqlalchemy import select, func
    from app.models.gst.gstn_models import GSTReturnFiling
    from decimal import Decimal

    query = select(GSTReturnFiling).where(
        GSTReturnFiling.organization_id == organization_id
    )
    if financial_year:
        query = query.where(GSTReturnFiling.financial_year == financial_year)

    result = await db.execute(query)
    filings = result.scalars().all()

    return {
        "total_returns": len(filings),
        "filed_on_time": sum(1 for f in filings if f.status == GSTReturnStatus.FILED and f.filing_date and f.due_date and f.filing_date <= f.due_date),
        "filed_late": sum(1 for f in filings if f.status == GSTReturnStatus.FILED and f.filing_date and f.due_date and f.filing_date > f.due_date),
        "pending": sum(1 for f in filings if f.status in [GSTReturnStatus.NOT_STARTED, GSTReturnStatus.DRAFT, GSTReturnStatus.VALIDATED]),
        "gstr1_count": sum(1 for f in filings if f.return_type == GSTReturnType.GSTR1),
        "gstr3b_count": sum(1 for f in filings if f.return_type == GSTReturnType.GSTR3B),
        "total_tax_liability": sum(f.total_tax_liability or Decimal("0") for f in filings),
        "total_itc_claimed": sum(f.total_itc_claimed or Decimal("0") for f in filings),
        "total_cash_paid": sum(f.cash_payment or Decimal("0") for f in filings),
        "total_late_fee": sum(f.late_fee or Decimal("0") for f in filings),
    }


@router.get(
    "/statistics/itc-reconciliation",
    summary="Get ITC reconciliation statistics",
    description="Get ITC reconciliation statistics.",
)
async def get_itc_statistics(
    organization_id: UUID,
    return_period: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("gstn.statistics.read")),
):
    """Get ITC reconciliation statistics."""
    from sqlalchemy import select, func
    from app.models.gst.gstn_models import GSTItcMismatch
    from decimal import Decimal

    query = select(GSTItcMismatch).where(
        GSTItcMismatch.organization_id == organization_id
    )
    if return_period:
        query = query.where(GSTItcMismatch.return_period == return_period)

    result = await db.execute(query)
    mismatches = result.scalars().all()

    return {
        "total_mismatches": len(mismatches),
        "pending_resolution": sum(1 for m in mismatches if m.resolution_status == ITCMismatchResolution.PENDING),
        "resolved": sum(1 for m in mismatches if m.resolution_status != ITCMismatchResolution.PENDING),
        "missing_in_2b": sum(1 for m in mismatches if m.mismatch_type == ITCMismatchType.MISSING_IN_2B),
        "missing_in_books": sum(1 for m in mismatches if m.mismatch_type == ITCMismatchType.MISSING_IN_BOOKS),
        "amount_mismatch": sum(1 for m in mismatches if m.mismatch_type == ITCMismatchType.AMOUNT_MISMATCH),
        "total_variance": sum(m.variance_total or Decimal("0") for m in mismatches),
    }
