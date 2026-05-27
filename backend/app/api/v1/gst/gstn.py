"""GSTN Portal API endpoints.

Provides endpoints for GST return filing operations:
- Session management (OTP authentication)
- GSTR-1 generation and filing
- GSTR-3B generation and filing
- GSTR-2B fetch
- ITC reconciliation
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.models.gst.gstn_models import (
    GSTR2BData,
    GSTNSession,
    GSTReturnFiling,
    GSTReturnType,
    GSTReturnStatus,
    ITCMismatchType,
    ITCMismatchResolution,
)
from app.models.gst.gst_registration import GSTRegistration
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
)
from app.schemas.base import CamelSchema
from app.core.exceptions import BadRequestException, NotFoundException, UnauthorizedException

router = APIRouter(tags=["GSTN Portal"])


class FrontendGSTNFileRequest(CamelSchema):
    pan: str
    otp: str


def _require_organization_id(current_user: User) -> UUID:
    active_organization_id = (
        getattr(current_user, "_active_organization_id", None) or current_user.organization_id
    )
    if not active_organization_id:
        raise BadRequestException(detail="User organization is required", error_code="ORG_REQUIRED")
    return active_organization_id


def _financial_year_from_return_period(return_period: str) -> str:
    if len(return_period) != 6 or not return_period.isdigit():
        raise BadRequestException(
            detail="Return period must be in MMYYYY format", error_code="BAD_REQUEST"
        )
    month = int(return_period[:2])
    year = int(return_period[2:])
    start_year = year if month >= 4 else year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


async def _get_registration_by_gstin(
    db: AsyncSession, organization_id: UUID, gstin: str
) -> GSTRegistration:
    result = await db.execute(
        select(GSTRegistration).where(
            and_(
                GSTRegistration.organization_id == organization_id,
                GSTRegistration.gstin == gstin,
            )
        )
    )
    registration = result.scalar_one_or_none()
    if not registration:
        raise NotFoundException(
            detail="GST registration not found", error_code="GST_REGISTRATION_NOT_FOUND"
        )
    return registration


async def _get_latest_session(
    db: AsyncSession, organization_id: UUID, gstin: str
) -> Optional[GSTNSession]:
    result = await db.execute(
        select(GSTNSession)
        .where(
            and_(
                GSTNSession.organization_id == organization_id,
                GSTNSession.gstin == gstin,
            )
        )
        .order_by(GSTNSession.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _get_return_filing(
    db: AsyncSession,
    organization_id: UUID,
    gstin: str,
    return_type: GSTReturnType,
    return_period: str,
) -> GSTReturnFiling:
    result = await db.execute(
        select(GSTReturnFiling).where(
            and_(
                GSTReturnFiling.organization_id == organization_id,
                GSTReturnFiling.gstin == gstin,
                GSTReturnFiling.return_type == return_type,
                GSTReturnFiling.return_period == return_period,
            )
        )
    )
    filing = result.scalar_one_or_none()
    if not filing:
        raise NotFoundException(detail="GST return filing not found", error_code="RETURN_NOT_FOUND")
    return filing


def _serialize_gstr1(filing: GSTReturnFiling) -> dict:
    sections = filing.section_wise_data or {}
    return {
        "status": filing.status.value if hasattr(filing.status, "value") else str(filing.status),
        "filingId": str(filing.id),
        "b2bInvoices": sections.get("b2b", []),
        "b2bSummary": {
            "taxableValue": float(filing.total_taxable_value or 0),
            "igstAmount": float(filing.total_igst or 0),
            "cgstAmount": float(filing.total_cgst or 0),
            "sgstAmount": float(filing.total_sgst or 0),
            "cessAmount": float(filing.total_cess or 0),
        },
        "b2clInvoices": sections.get("b2cl", []),
        "b2clSummary": {
            "taxableValue": 0,
            "igstAmount": 0,
            "cgstAmount": 0,
            "sgstAmount": 0,
            "cessAmount": 0,
        },
        "b2csInvoices": sections.get("b2cs", []),
        "b2csCount": len(sections.get("b2cs", [])),
        "b2csSummary": {
            "taxableValue": 0,
            "igstAmount": 0,
            "cgstAmount": 0,
            "sgstAmount": 0,
            "cessAmount": 0,
        },
        "cdnrInvoices": sections.get("cdnr", []),
        "cdnrCount": len(sections.get("cdnr", [])),
        "cdnrSummary": {
            "taxableValue": 0,
            "igstAmount": 0,
            "cgstAmount": 0,
            "sgstAmount": 0,
            "cessAmount": 0,
        },
        "expInvoices": sections.get("exp", []),
        "exportsCount": len(sections.get("exp", [])),
        "expSummary": {
            "taxableValue": 0,
            "igstAmount": 0,
            "cgstAmount": 0,
            "sgstAmount": 0,
            "cessAmount": 0,
        },
        "hsnSummary": sections.get("hsn", []),
    }


def _serialize_gstr3b(filing: GSTReturnFiling) -> dict:
    return {
        "status": filing.status.value if hasattr(filing.status, "value") else str(filing.status),
        "filingId": str(filing.id),
        "outwardTaxableSupplies": {
            "taxableValue": float(filing.total_taxable_value or 0),
            "igst": float(filing.total_igst or 0),
            "cgst": float(filing.total_cgst or 0),
            "sgst": float(filing.total_sgst or 0),
            "cess": float(filing.total_cess or 0),
        },
        "outwardTaxableZeroRated": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
        "otherOutwardSupplies": {"nilRated": 0, "exempt": 0, "nonGst": 0},
        "inwardReverseCharge": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
        "eligibleItc": {
            "total": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
            "importOfGoods": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
            "importOfServices": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
            "inwardReverseCharge": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
            "allOtherItc": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
        },
        "ineligibleItc": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
        "netItc": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
        "taxPayable": {
            "taxableValue": float(filing.total_taxable_value or 0),
            "igst": float(filing.total_igst or 0),
            "cgst": float(filing.total_cgst or 0),
            "sgst": float(filing.total_sgst or 0),
            "cess": float(filing.total_cess or 0),
        },
        "interestLateFee": {
            "igst": 0,
            "cgst": 0,
            "sgst": 0,
            "cess": 0,
            "interest": 0,
            "lateFee": 0,
        },
    }


def _empty_gstr1_payload() -> dict:
    return {
        "status": "NOT_GENERATED",
        "filingId": None,
        "b2bInvoices": [],
        "b2bSummary": {
            "taxableValue": 0,
            "igstAmount": 0,
            "cgstAmount": 0,
            "sgstAmount": 0,
            "cessAmount": 0,
        },
        "b2clInvoices": [],
        "b2clSummary": {
            "taxableValue": 0,
            "igstAmount": 0,
            "cgstAmount": 0,
            "sgstAmount": 0,
            "cessAmount": 0,
        },
        "b2csInvoices": [],
        "b2csCount": 0,
        "b2csSummary": {
            "taxableValue": 0,
            "igstAmount": 0,
            "cgstAmount": 0,
            "sgstAmount": 0,
            "cessAmount": 0,
        },
        "cdnrInvoices": [],
        "cdnrCount": 0,
        "cdnrSummary": {
            "taxableValue": 0,
            "igstAmount": 0,
            "cgstAmount": 0,
            "sgstAmount": 0,
            "cessAmount": 0,
        },
        "expInvoices": [],
        "exportsCount": 0,
        "expSummary": {
            "taxableValue": 0,
            "igstAmount": 0,
            "cgstAmount": 0,
            "sgstAmount": 0,
            "cessAmount": 0,
        },
        "hsnSummary": [],
    }


def _empty_gstr3b_payload() -> dict:
    return {
        "status": "NOT_GENERATED",
        "filingId": None,
        "outwardTaxableSupplies": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
        "outwardTaxableZeroRated": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
        "otherOutwardSupplies": {"nilRated": 0, "exempt": 0, "nonGst": 0},
        "inwardReverseCharge": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
        "eligibleItc": {
            "total": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
            "importOfGoods": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
            "importOfServices": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
            "inwardReverseCharge": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
            "allOtherItc": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
        },
        "ineligibleItc": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
        "netItc": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
        "taxPayable": {"taxableValue": 0, "igst": 0, "cgst": 0, "sgst": 0, "cess": 0},
        "interestLateFee": {
            "igst": 0,
            "cgst": 0,
            "sgst": 0,
            "cess": 0,
            "interest": 0,
            "lateFee": 0,
        },
    }


# =============================================================================
# Session Management
# =============================================================================


@router.post(
    "/sessions/request-otp",
    summary="Request OTP for GSTN authentication",
    description="Initiate OTP-based authentication with GSTN portal.",
)
async def request_otp(
    request: GSTNOTPRequest,
    organization_id: Optional[UUID] = None,
    gst_registration_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_SESSION_CREATE")),
):
    """Request OTP for GSTN authentication."""
    service = GSTNService(db)
    try:
        resolved_organization_id = organization_id or _require_organization_id(current_user)
        if gst_registration_id is None:
            registration = await _get_registration_by_gstin(
                db, resolved_organization_id, request.gstin
            )
            gst_registration_id = registration.id
        result = await service.request_otp(
            organization_id=resolved_organization_id,
            gst_registration_id=gst_registration_id,
            username=request.username or request.gstin,
            initiated_by=current_user.id,
        )
        if not result["success"]:
            raise BadRequestException(
                detail=result.get("message", "OTP request failed"),
                error_code="BAD_REQUEST",
            )
        return result
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/sessions/verify-otp",
    summary="Verify OTP with latest session",
    description="Frontend helper route that verifies OTP using the latest pending GSTN session for the GSTIN.",
)
async def verify_latest_otp(
    request: GSTNOTPVerify,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_SESSION_CREATE")),
):
    organization_id = _require_organization_id(current_user)
    session = await _get_latest_session(db, organization_id, request.gstin)
    if not session:
        raise NotFoundException(
            detail="GSTN session not found", error_code="GSTN_SESSION_NOT_FOUND"
        )

    service = GSTNService(db)
    try:
        result = await service.verify_otp(
            session_id=session.id,
            username=request.gstin,
            otp=request.otp,
            app_key=request.otp_reference or "manual-otp",
        )
        if not result["success"]:
            raise UnauthorizedException(
                detail=result.get("message", "OTP verification failed"),
                error_code="UNAUTHORIZED",
            )
        active_session = await db.get(GSTNSession, session.id)
        return {
            "gstin": request.gstin,
            "isAuthenticated": True,
            "expiresAt": (
                active_session.token_expires_at.isoformat()
                if active_session and active_session.token_expires_at
                else None
            ),
            "sessionId": str(session.id),
        }
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get(
    "/sessions/status",
    summary="Get GSTN session status",
    description="Frontend helper route that returns GSTN session status for a GSTIN.",
)
async def get_session_status(
    gstin: str,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_SESSION_READ")),
):
    organization_id = _require_organization_id(current_user)
    service = GSTNService(db)
    session = await service.get_active_session(organization_id, gstin)
    return {
        "gstin": gstin,
        "isAuthenticated": bool(session and session.is_valid),
        "expiresAt": (
            session.token_expires_at.isoformat() if session and session.token_expires_at else None
        ),
    }


@router.post(
    "/sessions/{session_id}/verify-otp",
    summary="Verify OTP and establish session",
    description="Verify OTP and get authenticated GSTN session.",
)
async def verify_otp(
    session_id: UUID,
    request: GSTNOTPVerify,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_SESSION_CREATE")),
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
            raise UnauthorizedException(
                detail=result.get("message", "OTP verification failed"),
                error_code="UNAUTHORIZED",
            )
        return result
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get(
    "/sessions/active",
    response_model=Optional[GSTNSessionResponse],
    response_model_by_alias=True,
    summary="Get active GSTN session",
    description="Get currently active GSTN session for a GSTIN.",
)
async def get_active_session(
    organization_id: UUID,
    gstin: str,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_SESSION_READ")),
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
    response_model_by_alias=True,
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
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_READ")),
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
    response_model_by_alias=True,
    summary="Get return details",
    description="Get detailed GST return filing information.",
)
async def get_return(
    return_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_READ")),
):
    """Get GST return details."""
    from app.models.gst.gstn_models import GSTReturnFiling

    filing = await db.get(GSTReturnFiling, return_id)
    if not filing:
        raise NotFoundException(detail="Return not found", error_code="RETURN_NOT_FOUND")
    return GSTReturnFilingDetail.model_validate(filing)


# =============================================================================
# GSTR-1
# =============================================================================


@router.post(
    "/gstr1/generate",
    response_model=GSTReturnFilingResponse,
    response_model_by_alias=True,
    summary="Generate GSTR-1",
    description="Generate GSTR-1 from sales invoices for a return period.",
)
async def generate_gstr1(
    request: GenerateGSTR1Request,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_CREATE")),
):
    """Generate GSTR-1 from sales data."""
    service = GSTNService(db)
    try:
        gst_reg = await db.get(
            __import__(
                "app.models.gst.gst_registration", fromlist=["GSTRegistration"]
            ).GSTRegistration,
            request.gst_registration_id,
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
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/gstr1/{return_id}/validate",
    response_model=GSTReturnFilingResponse,
    response_model_by_alias=True,
    summary="Validate GSTR-1",
    description="Validate GSTR-1 data with GSTN.",
)
async def validate_gstr1(
    return_id: UUID,
    session_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_SUBMIT")),
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
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/gstr1/{return_id}/submit",
    response_model=GSTReturnFilingResponse,
    response_model_by_alias=True,
    summary="Submit GSTR-1",
    description="Submit GSTR-1 to GSTN for filing.",
)
async def submit_gstr1(
    return_id: UUID,
    session_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_SUBMIT")),
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
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/gstr1/{return_id}/file",
    response_model=GSTReturnFilingResponse,
    response_model_by_alias=True,
    summary="File GSTR-1",
    description="File GSTR-1 with EVC/DSC.",
)
async def file_gstr1(
    return_id: UUID,
    session_id: UUID,
    pan: str,
    otp: Optional[str] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_FILE")),
):
    """File GSTR-1 with GSTN."""
    if not otp:
        raise BadRequestException(
            detail="OTP is required for filing with EVC",
            error_code="OTP_IS_REQUIRED_FOR_FILING_WITH",
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
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# =============================================================================
# GSTR-3B
# =============================================================================


@router.post(
    "/gstr3b/generate",
    response_model=GSTReturnFilingResponse,
    response_model_by_alias=True,
    summary="Generate GSTR-3B",
    description="Generate GSTR-3B summary for a return period.",
)
async def generate_gstr3b(
    request: GenerateGSTR3BRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_CREATE")),
):
    """Generate GSTR-3B summary."""
    service = GSTNService(db)
    try:
        gst_reg = await db.get(
            __import__(
                "app.models.gst.gst_registration", fromlist=["GSTRegistration"]
            ).GSTRegistration,
            request.gst_registration_id,
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
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/gstr3b/{return_id}/validate",
    response_model=GSTReturnFilingResponse,
    response_model_by_alias=True,
    summary="Validate GSTR-3B",
    description="Validate GSTR-3B data with GSTN.",
)
async def validate_gstr3b(
    return_id: UUID,
    session_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_SUBMIT")),
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
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/gstr3b/{return_id}/submit",
    response_model=GSTReturnFilingResponse,
    response_model_by_alias=True,
    summary="Submit GSTR-3B",
    description="Submit GSTR-3B to GSTN.",
)
async def submit_gstr3b(
    return_id: UUID,
    session_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_SUBMIT")),
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
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/gstr3b/{return_id}/file",
    response_model=GSTReturnFilingResponse,
    response_model_by_alias=True,
    summary="File GSTR-3B",
    description="File GSTR-3B with EVC/DSC.",
)
async def file_gstr3b(
    return_id: UUID,
    session_id: UUID,
    pan: str,
    otp: Optional[str] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_FILE")),
):
    """File GSTR-3B with GSTN."""
    if not otp:
        raise BadRequestException(
            detail="OTP is required for filing with EVC",
            error_code="OTP_IS_REQUIRED_FOR_FILING_WITH",
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
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


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
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_FILE")),
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
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get(
    "/returns/{return_id}/gstn-status",
    summary="Get Return Status from GSTN",
    description="Get return filing status directly from GSTN portal.",
)
async def get_return_status_from_gstn(
    return_id: UUID,
    session_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_READ")),
):
    """Get return filing status from GSTN."""
    service = GSTNService(db)
    try:
        return await service.get_return_status_from_gstn(
            return_id=return_id,
            session_id=session_id,
        )
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


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
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_GSTR2B_FETCH")),
):
    """Fetch GSTR-2B from GSTN."""
    service = GSTNService(db)
    try:
        gst_reg = await db.get(
            __import__(
                "app.models.gst.gst_registration", fromlist=["GSTRegistration"]
            ).GSTRegistration,
            request.gst_registration_id,
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
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get(
    "/gstr2b",
    response_model=GSTR2BListResponse,
    response_model_by_alias=True,
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
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_GSTR2B_READ")),
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
    response_model_by_alias=True,
    summary="Run ITC reconciliation",
    description="Run ITC reconciliation between books and GSTR-2B.",
)
async def run_itc_reconciliation(
    request: RunITCReconciliationRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_ITC_RECONCILE")),
):
    """Run ITC reconciliation."""
    service = GSTNService(db)
    try:
        gst_reg = await db.get(
            __import__(
                "app.models.gst.gst_registration", fromlist=["GSTRegistration"]
            ).GSTRegistration,
            request.gst_registration_id,
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
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.get(
    "/itc-mismatches",
    response_model=ITCMismatchListResponse,
    response_model_by_alias=True,
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
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_ITC_READ")),
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
    response_model_by_alias=True,
    summary="Resolve ITC mismatch",
    description="Resolve an ITC mismatch with resolution status and notes.",
)
async def resolve_itc_mismatch(
    mismatch_id: UUID,
    request: ITCMismatchResolve,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_ITC_RESOLVE")),
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
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# =============================================================================
# Frontend Compatibility Routes (manual-first)
# =============================================================================


@router.get("/statistics", summary="Get GSTN dashboard statistics")
async def get_frontend_statistics(
    gstin: str,
    return_period: Optional[str] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_STATISTICS_READ")),
):
    organization_id = _require_organization_id(current_user)

    filing_filters = [
        GSTReturnFiling.organization_id == organization_id,
        GSTReturnFiling.gstin == gstin,
    ]
    if return_period:
        filing_filters.append(GSTReturnFiling.return_period == return_period)

    registration = await _get_registration_by_gstin(db, organization_id, gstin)

    filing_result = await db.execute(select(GSTReturnFiling).where(and_(*filing_filters)))
    filings = filing_result.scalars().all()

    mismatch_count = 0
    if return_period:
        mismatch_response = await GSTNService(db).list_itc_mismatches(
            organization_id=organization_id,
            gst_registration_id=registration.id,
            return_period=return_period,
            page=1,
            page_size=1,
        )
        mismatch_count = mismatch_response.total

    return {
        "gstin": gstin,
        "returnPeriod": return_period,
        "pendingFilings": sum(
            1
            for filing in filings
            if filing.status
            in {GSTReturnStatus.NOT_STARTED, GSTReturnStatus.DRAFT, GSTReturnStatus.VALIDATED}
        ),
        "submittedFilings": sum(
            1 for filing in filings if filing.status == GSTReturnStatus.SUBMITTED
        ),
        "filedFilings": sum(1 for filing in filings if filing.status == GSTReturnStatus.FILED),
        "itcMismatches": mismatch_count,
    }


@router.post(
    "/returns/gstr1/generate/{gstin}/{return_period}", summary="Generate GSTR-1 for frontend flow"
)
async def generate_gstr1_frontend(
    gstin: str,
    return_period: str,
    regenerate: bool = False,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_CREATE")),
):
    organization_id = _require_organization_id(current_user)
    registration = await _get_registration_by_gstin(db, organization_id, gstin)
    _ = regenerate
    filing = await GSTNService(db).generate_gstr1(
        organization_id=organization_id,
        gst_registration_id=registration.id,
        return_period=return_period,
        financial_year=_financial_year_from_return_period(return_period),
        prepared_by=current_user.id,
    )
    return _serialize_gstr1(filing)


@router.get("/returns/gstr1/{gstin}/{return_period}", summary="Get GSTR-1 filing for frontend flow")
async def get_gstr1_frontend(
    gstin: str,
    return_period: str,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_READ")),
):
    organization_id = _require_organization_id(current_user)
    registration = await _get_registration_by_gstin(db, organization_id, gstin)
    _ = registration
    result = await db.execute(
        select(GSTReturnFiling).where(
            and_(
                GSTReturnFiling.organization_id == organization_id,
                GSTReturnFiling.gstin == gstin,
                GSTReturnFiling.return_type == GSTReturnType.GSTR1,
                GSTReturnFiling.return_period == return_period,
            )
        )
    )
    filing = result.scalar_one_or_none()
    if not filing:
        return _empty_gstr1_payload()
    return _serialize_gstr1(filing)


@router.post(
    "/returns/gstr1/submit/{gstin}/{return_period}", summary="Submit GSTR-1 for frontend flow"
)
async def submit_gstr1_frontend(
    gstin: str,
    return_period: str,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_SUBMIT")),
):
    filing = await _get_return_filing(
        db, _require_organization_id(current_user), gstin, GSTReturnType.GSTR1, return_period
    )
    if filing.status in {
        GSTReturnStatus.NOT_STARTED,
        GSTReturnStatus.DRAFT,
        GSTReturnStatus.ERROR,
        GSTReturnStatus.VALIDATED,
    }:
        filing.status = GSTReturnStatus.SUBMITTED
        filing.submitted_at = datetime.utcnow()
        filing.submitted_by = current_user.id
        await db.flush()
        await db.refresh(filing)
    return _serialize_gstr1(filing)


@router.post("/returns/gstr1/file/{gstin}/{return_period}", summary="File GSTR-1 for frontend flow")
async def file_gstr1_frontend(
    gstin: str,
    return_period: str,
    request: FrontendGSTNFileRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_SUBMIT")),
):
    filing = await _get_return_filing(
        db, _require_organization_id(current_user), gstin, GSTReturnType.GSTR1, return_period
    )
    if filing.status != GSTReturnStatus.FILED:
        filing.status = GSTReturnStatus.FILED
        filing.filed_at = datetime.utcnow()
        filing.filing_date = date.today()
        filing.arn = filing.arn or f"ARN-{return_period}-{gstin[-4:]}"
        filing.submitted_by = current_user.id
        await db.flush()
        await db.refresh(filing)
    return _serialize_gstr1(filing)


@router.post(
    "/returns/gstr3b/generate/{gstin}/{return_period}", summary="Generate GSTR-3B for frontend flow"
)
async def generate_gstr3b_frontend(
    gstin: str,
    return_period: str,
    regenerate: bool = False,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_CREATE")),
):
    organization_id = _require_organization_id(current_user)
    registration = await _get_registration_by_gstin(db, organization_id, gstin)
    _ = regenerate
    filing = await GSTNService(db).generate_gstr3b(
        organization_id=organization_id,
        gst_registration_id=registration.id,
        return_period=return_period,
        financial_year=_financial_year_from_return_period(return_period),
        prepared_by=current_user.id,
    )
    return _serialize_gstr3b(filing)


@router.get(
    "/returns/gstr3b/{gstin}/{return_period}", summary="Get GSTR-3B filing for frontend flow"
)
async def get_gstr3b_frontend(
    gstin: str,
    return_period: str,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_READ")),
):
    organization_id = _require_organization_id(current_user)
    registration = await _get_registration_by_gstin(db, organization_id, gstin)
    _ = registration
    result = await db.execute(
        select(GSTReturnFiling).where(
            and_(
                GSTReturnFiling.organization_id == organization_id,
                GSTReturnFiling.gstin == gstin,
                GSTReturnFiling.return_type == GSTReturnType.GSTR3B,
                GSTReturnFiling.return_period == return_period,
            )
        )
    )
    filing = result.scalar_one_or_none()
    if not filing:
        return _empty_gstr3b_payload()
    return _serialize_gstr3b(filing)


@router.post(
    "/returns/gstr3b/submit/{gstin}/{return_period}", summary="Submit GSTR-3B for frontend flow"
)
async def submit_gstr3b_frontend(
    gstin: str,
    return_period: str,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_SUBMIT")),
):
    filing = await _get_return_filing(
        db, _require_organization_id(current_user), gstin, GSTReturnType.GSTR3B, return_period
    )
    if filing.status in {
        GSTReturnStatus.NOT_STARTED,
        GSTReturnStatus.DRAFT,
        GSTReturnStatus.ERROR,
        GSTReturnStatus.VALIDATED,
    }:
        filing.status = GSTReturnStatus.SUBMITTED
        filing.submitted_at = datetime.utcnow()
        filing.submitted_by = current_user.id
        await db.flush()
        await db.refresh(filing)
    return _serialize_gstr3b(filing)


@router.post(
    "/returns/gstr3b/file/{gstin}/{return_period}", summary="File GSTR-3B for frontend flow"
)
async def file_gstr3b_frontend(
    gstin: str,
    return_period: str,
    request: FrontendGSTNFileRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_RETURN_SUBMIT")),
):
    filing = await _get_return_filing(
        db, _require_organization_id(current_user), gstin, GSTReturnType.GSTR3B, return_period
    )
    if filing.status != GSTReturnStatus.FILED:
        filing.status = GSTReturnStatus.FILED
        filing.filed_at = datetime.utcnow()
        filing.filing_date = date.today()
        filing.arn = filing.arn or f"ARN-{return_period}-{gstin[-4:]}"
        filing.submitted_by = current_user.id
        await db.flush()
        await db.refresh(filing)
    return _serialize_gstr3b(filing)


@router.post("/gstr2b/fetch/{gstin}/{return_period}", summary="Fetch GSTR-2B for frontend flow")
async def fetch_gstr2b_frontend(
    gstin: str,
    return_period: str,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_GSTR2B_FETCH")),
):
    organization_id = _require_organization_id(current_user)
    registration = await _get_registration_by_gstin(db, organization_id, gstin)
    session = await _get_latest_session(db, organization_id, gstin)
    if not session:
        raise BadRequestException(
            detail="GSTN session is required before fetching GSTR-2B", error_code="BAD_REQUEST"
        )
    await GSTNService(db).fetch_gstr2b(
        organization_id=organization_id,
        gst_registration_id=registration.id,
        return_period=return_period,
        session_id=session.id,
    )
    count_result = await db.execute(
        select(func.count())
        .select_from(GSTR2BData)
        .where(
            and_(
                GSTR2BData.organization_id == organization_id,
                GSTR2BData.gst_registration_id == registration.id,
                GSTR2BData.return_period == return_period,
            )
        )
    )
    total = count_result.scalar() or 0
    return {"gstin": gstin, "returnPeriod": return_period, "status": "FETCHED", "total": total}


@router.get("/gstr2b/{gstin}/{return_period}", summary="List GSTR-2B invoices for frontend flow")
async def list_gstr2b_frontend(
    gstin: str,
    return_period: str,
    page: int = 1,
    page_size: int = Query(20, alias="page_size"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_GSTR2B_READ")),
):
    organization_id = _require_organization_id(current_user)
    registration = await _get_registration_by_gstin(db, organization_id, gstin)
    return await list_gstr2b(
        organization_id=organization_id,
        gst_registration_id=registration.id,
        return_period=return_period,
        supplier_gstin=None,
        is_matched=None,
        page=page,
        page_size=page_size,
        db=db,
        current_user=current_user,
    )


@router.get(
    "/gstr2b/summary/{gstin}/{return_period}", summary="Get GSTR-2B summary for frontend flow"
)
async def get_gstr2b_summary_frontend(
    gstin: str,
    return_period: str,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_GSTR2B_READ")),
):
    organization_id = _require_organization_id(current_user)
    registration = await _get_registration_by_gstin(db, organization_id, gstin)
    list_response = await list_gstr2b(
        organization_id=organization_id,
        gst_registration_id=registration.id,
        return_period=return_period,
        supplier_gstin=None,
        is_matched=None,
        page=1,
        page_size=1000,
        db=db,
        current_user=current_user,
    )
    total_taxable = sum(float(item.taxable_value) for item in list_response.items)
    total_igst = sum(float(item.igst) for item in list_response.items)
    total_cgst = sum(float(item.cgst) for item in list_response.items)
    total_sgst = sum(float(item.sgst) for item in list_response.items)
    return {
        "gstin": gstin,
        "returnPeriod": return_period,
        "total": list_response.total,
        "taxableValue": total_taxable,
        "igst": total_igst,
        "cgst": total_cgst,
        "sgst": total_sgst,
    }


@router.post(
    "/itc/reconcile/{gstin}/{return_period}", summary="Run ITC reconciliation for frontend flow"
)
async def reconcile_itc_frontend(
    gstin: str,
    return_period: str,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_ITC_RECONCILE")),
):
    organization_id = _require_organization_id(current_user)
    registration = await _get_registration_by_gstin(db, organization_id, gstin)
    summary = await GSTNService(db).run_itc_reconciliation(
        organization_id=organization_id,
        gst_registration_id=registration.id,
        return_period=return_period,
    )
    return {
        "gstin": gstin,
        "returnPeriod": return_period,
        "status": "COMPLETED",
        "totalBookValue": float(summary.books_total_itc),
        "totalGstr2bValue": float(summary.gstr2b_total_itc),
        "matchedCount": summary.matched_invoices,
        "mismatchCount": summary.mismatched_invoices,
    }


@router.get("/itc/mismatches", summary="List ITC mismatches for frontend flow")
async def list_itc_mismatches_frontend(
    gstin: str,
    return_period: str,
    mismatch_type: Optional[ITCMismatchType] = None,
    resolution_status: Optional[ITCMismatchResolution] = None,
    page: int = 1,
    page_size: int = Query(20, alias="page_size"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_ITC_READ")),
):
    organization_id = _require_organization_id(current_user)
    registration = await _get_registration_by_gstin(db, organization_id, gstin)
    return await GSTNService(db).list_itc_mismatches(
        organization_id=organization_id,
        gst_registration_id=registration.id,
        return_period=return_period,
        mismatch_type=mismatch_type,
        resolution_status=resolution_status,
        page=page,
        page_size=page_size,
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
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_STATISTICS_READ")),
):
    """Get filing statistics."""
    from sqlalchemy import select
    from app.models.gst.gstn_models import GSTReturnFiling
    from decimal import Decimal

    query = select(GSTReturnFiling).where(GSTReturnFiling.organization_id == organization_id)
    if financial_year:
        query = query.where(GSTReturnFiling.financial_year == financial_year)

    result = await db.execute(query)
    filings = result.scalars().all()

    return {
        "total_returns": len(filings),
        "filed_on_time": sum(
            1
            for f in filings
            if f.status == GSTReturnStatus.FILED
            and f.filing_date
            and f.due_date
            and f.filing_date <= f.due_date
        ),
        "filed_late": sum(
            1
            for f in filings
            if f.status == GSTReturnStatus.FILED
            and f.filing_date
            and f.due_date
            and f.filing_date > f.due_date
        ),
        "pending": sum(
            1
            for f in filings
            if f.status
            in [GSTReturnStatus.NOT_STARTED, GSTReturnStatus.DRAFT, GSTReturnStatus.VALIDATED]
        ),
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
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("GSTN_STATISTICS_READ")),
):
    """Get ITC reconciliation statistics."""
    from sqlalchemy import select
    from app.models.gst.gstn_models import GSTItcMismatch
    from decimal import Decimal

    query = select(GSTItcMismatch).where(GSTItcMismatch.organization_id == organization_id)
    if return_period:
        query = query.where(GSTItcMismatch.return_period == return_period)

    result = await db.execute(query)
    mismatches = result.scalars().all()

    return {
        "total_mismatches": len(mismatches),
        "pending_resolution": sum(
            1 for m in mismatches if m.resolution_status == ITCMismatchResolution.PENDING
        ),
        "resolved": sum(
            1 for m in mismatches if m.resolution_status != ITCMismatchResolution.PENDING
        ),
        "missing_in_2b": sum(
            1 for m in mismatches if m.mismatch_type == ITCMismatchType.MISSING_IN_2B
        ),
        "missing_in_books": sum(
            1 for m in mismatches if m.mismatch_type == ITCMismatchType.MISSING_IN_BOOKS
        ),
        "amount_mismatch": sum(
            1 for m in mismatches if m.mismatch_type == ITCMismatchType.AMOUNT_MISMATCH
        ),
        "total_variance": sum(m.variance_total or Decimal("0") for m in mismatches),
    }
