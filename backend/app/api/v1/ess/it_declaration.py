"""ESS IT Declaration API endpoints (Indian Income Tax)."""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ESSUserContext, get_current_ess_user, get_ess_db_with_tenant
from app.services.ess.it_declaration_service import ESSITDeclarationService
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter(prefix="/it-declaration", tags=["ESS IT Declaration"])


async def _get_owned_declaration(
    service: ESSITDeclarationService,
    declaration_id: UUID,
    employee_id: UUID,
):
    """Return a declaration only if it belongs to the authenticated employee."""
    declaration = await service.get_declaration_by_id(declaration_id)
    if not declaration or declaration.employee_id != employee_id:
        raise NotFoundException("Declaration not found")
    return declaration


# ==================== Schemas ====================


class ITSectionResponse(BaseModel):
    """IT declaration section response."""

    id: str
    section_code: str
    section_name: str
    description: Optional[str]
    category: str
    max_limit: float
    requires_proof: bool
    applicable_in_old_regime: bool
    applicable_in_new_regime: bool
    help_text: Optional[str]


class DeclarationItemCreate(BaseModel):
    """Create declaration item."""

    section_code: str
    particular: str
    declared_amount: Decimal = Field(..., gt=0)
    description: Optional[str] = None
    investment_date: Optional[date] = None
    policy_number: Optional[str] = None
    institution_name: Optional[str] = None
    proof_url: Optional[str] = None
    proof_type: Optional[str] = None


class DeclarationItemUpdate(BaseModel):
    """Update declaration item."""

    particular: Optional[str] = None
    declared_amount: Optional[Decimal] = None
    description: Optional[str] = None
    investment_date: Optional[date] = None
    policy_number: Optional[str] = None
    institution_name: Optional[str] = None
    proof_url: Optional[str] = None
    proof_type: Optional[str] = None


class HRADetailsUpdate(BaseModel):
    """Update HRA details."""

    rent_paid_monthly: Decimal
    landlord_name: str
    landlord_pan: Optional[str] = None
    landlord_address: Optional[str] = None
    metro_city: bool = False


class HRAReceiptCreate(BaseModel):
    """Create HRA receipt."""

    month: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    rent_amount: Decimal
    receipt_number: Optional[str] = None
    receipt_url: Optional[str] = None


class HomeLoanDetailsUpdate(BaseModel):
    """Update home loan details."""

    home_loan_interest: Decimal
    home_loan_principal: Optional[Decimal] = None
    loan_sanctioned_date: Optional[date] = None
    lender_name: Optional[str] = None
    lender_pan: Optional[str] = None
    property_type: str = "SELF_OCCUPIED"


class TaxCalculationRequest(BaseModel):
    """Tax calculation request."""

    gross_salary: Decimal
    other_income: Decimal = Decimal("0")


class DeclarationItemResponse(BaseModel):
    """Declaration item response."""

    id: str
    section_code: str
    particular: str
    declared_amount: float
    verified_amount: Optional[float]
    approved_amount: Optional[float]
    proof_submitted: bool
    is_verified: bool


class DeclarationSummaryResponse(BaseModel):
    """Declaration summary response."""

    id: str
    financial_year: str
    tax_regime: str
    total_declared_amount: float
    total_verified_amount: float
    total_approved_amount: float
    status: str
    version: int


class DeclarationDetailResponse(DeclarationSummaryResponse):
    """Detailed declaration response."""

    hra_declared: Optional[float]
    rent_paid_monthly: Optional[float]
    landlord_name: Optional[str]
    metro_city: bool
    home_loan_interest: Optional[float]
    home_loan_principal: Optional[float]
    property_type: Optional[str]
    estimated_taxable_income: Optional[float]
    estimated_tax_liability: Optional[float]
    monthly_tds: Optional[float]
    submitted_date: Optional[str]
    verified_date: Optional[str]
    items: List[DeclarationItemResponse]


class TaxCalculationResponse(BaseModel):
    """Tax calculation response."""

    gross_salary: float
    other_income: float
    total_deductions: float
    taxable_income: float
    tax_on_income: float
    surcharge: float
    cess: float
    total_tax: float
    monthly_tds: float
    tax_regime: str


class RegularizationCreate(BaseModel):
    """Create attendance regularization."""

    attendance_date: date
    regularization_type: str
    reason: str
    requested_in_time: Optional[str] = None
    requested_out_time: Optional[str] = None
    supporting_document: Optional[str] = None


class RegularizationResponse(BaseModel):
    """Regularization response."""

    id: str
    request_number: str
    attendance_date: date
    regularization_type: str
    reason: str
    status: str
    approved_by: Optional[str]
    approved_date: Optional[str]
    approver_remarks: Optional[str]
    created_at: str


# ==================== Endpoints ====================


@router.get("/sections", response_model=List[ITSectionResponse], response_model_by_alias=True)
async def get_sections(
    tax_regime: str = Query("OLD", pattern="^(OLD|NEW)$"),
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Get IT declaration sections for the tax regime."""
    service = ESSITDeclarationService(session)
    sections = await service.get_declaration_sections(
        organization_id=ess_context.organization_id,
        tax_regime=tax_regime,
    )

    return [
        ITSectionResponse(
            id=str(s.id),
            section_code=s.section_code,
            section_name=s.section_name,
            description=s.description,
            category=s.category,
            max_limit=float(s.max_limit),
            requires_proof=s.requires_proof,
            applicable_in_old_regime=s.applicable_in_old_regime,
            applicable_in_new_regime=s.applicable_in_new_regime,
            help_text=s.help_text,
        )
        for s in sections
    ]


@router.get("", response_model=List[DeclarationSummaryResponse], response_model_by_alias=True)
async def get_declarations(
    limit: int = Query(5, le=10),
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Get IT declarations for the employee."""
    service = ESSITDeclarationService(session)
    declarations = await service.get_declarations_by_employee(
        employee_id=ess_context.employee_id,
        limit=limit,
    )

    return [
        DeclarationSummaryResponse(
            id=str(d.id),
            financial_year=d.financial_year,
            tax_regime=d.tax_regime,
            total_declared_amount=float(d.total_declared_amount),
            total_verified_amount=float(d.total_verified_amount),
            total_approved_amount=float(d.total_approved_amount),
            status=d.status.value,
            version=d.version,
        )
        for d in declarations
    ]


@router.post(
    "/{financial_year}", response_model=DeclarationDetailResponse, response_model_by_alias=True
)
async def get_or_create_declaration(
    financial_year: str,
    tax_regime: str = Query("OLD", pattern="^(OLD|NEW)$"),
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Get or create declaration for a financial year."""
    service = ESSITDeclarationService(session)

    declaration = await service.get_or_create_declaration(
        organization_id=ess_context.organization_id,
        ess_user_id=ess_context.ess_user_id,
        employee_id=ess_context.employee_id,
        financial_year=financial_year,
        tax_regime=tax_regime,
    )

    await session.commit()

    return _format_declaration_detail(declaration)


@router.get(
    "/{declaration_id}/detail",
    response_model=DeclarationDetailResponse,
    response_model_by_alias=True,
)
async def get_declaration_detail(
    declaration_id: UUID,
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Get declaration details."""
    service = ESSITDeclarationService(session)
    declaration = await _get_owned_declaration(service, declaration_id, ess_context.employee_id)

    return _format_declaration_detail(declaration)


@router.patch("/{declaration_id}/regime")
async def update_tax_regime(
    declaration_id: UUID,
    tax_regime: str = Query(..., pattern="^(OLD|NEW)$"),
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Update tax regime for a declaration."""
    service = ESSITDeclarationService(session)
    await _get_owned_declaration(service, declaration_id, ess_context.employee_id)

    try:
        declaration = await service.update_tax_regime(declaration_id, tax_regime)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    if not declaration:
        raise NotFoundException(detail="Declaration not found", error_code="DECLARATION_NOT_FOUND")

    await session.commit()

    return {"success": True, "tax_regime": tax_regime}


# ==================== Declaration Items ====================


@router.post(
    "/{declaration_id}/items", response_model=DeclarationItemResponse, response_model_by_alias=True
)
async def add_declaration_item(
    declaration_id: UUID,
    request: DeclarationItemCreate,
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Add a declaration item."""
    service = ESSITDeclarationService(session)
    await _get_owned_declaration(service, declaration_id, ess_context.employee_id)

    try:
        item = await service.add_declaration_item(
            declaration_id=declaration_id, **request.model_dump()
        )
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    await session.commit()

    return DeclarationItemResponse(
        id=str(item.id),
        section_code=item.section_code,
        particular=item.particular,
        declared_amount=float(item.declared_amount),
        verified_amount=float(item.verified_amount) if item.verified_amount else None,
        approved_amount=float(item.approved_amount) if item.approved_amount else None,
        proof_submitted=item.proof_submitted,
        is_verified=item.is_verified,
    )


@router.patch(
    "/{declaration_id}/items/{item_id}",
    response_model=DeclarationItemResponse,
    response_model_by_alias=True,
)
async def update_declaration_item(
    declaration_id: UUID,
    item_id: UUID,
    request: DeclarationItemUpdate,
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Update a declaration item."""
    service = ESSITDeclarationService(session)
    await _get_owned_declaration(service, declaration_id, ess_context.employee_id)

    try:
        item = await service.update_declaration_item(
            item_id=item_id, **request.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    if not item:
        raise NotFoundException(detail="Item not found", error_code="ITEM_NOT_FOUND")

    await session.commit()

    return DeclarationItemResponse(
        id=str(item.id),
        section_code=item.section_code,
        particular=item.particular,
        declared_amount=float(item.declared_amount),
        verified_amount=float(item.verified_amount) if item.verified_amount else None,
        approved_amount=float(item.approved_amount) if item.approved_amount else None,
        proof_submitted=item.proof_submitted,
        is_verified=item.is_verified,
    )


@router.delete("/{declaration_id}/items/{item_id}")
async def delete_declaration_item(
    declaration_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Delete a declaration item."""
    service = ESSITDeclarationService(session)
    await _get_owned_declaration(service, declaration_id, ess_context.employee_id)

    try:
        success = await service.delete_declaration_item(item_id)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    if not success:
        raise NotFoundException(detail="Item not found", error_code="ITEM_NOT_FOUND")

    await session.commit()

    return {"success": True}


# ==================== HRA & Home Loan ====================


@router.put("/{declaration_id}/hra")
async def update_hra_details(
    declaration_id: UUID,
    request: HRADetailsUpdate,
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Update HRA details."""
    service = ESSITDeclarationService(session)
    await _get_owned_declaration(service, declaration_id, ess_context.employee_id)

    try:
        declaration = await service.update_hra_details(
            declaration_id=declaration_id, **request.model_dump()
        )
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    await session.commit()

    return {"success": True, "hra_declared": float(declaration.hra_declared)}


@router.post("/{declaration_id}/hra-receipts")
async def add_hra_receipt(
    declaration_id: UUID,
    request: HRAReceiptCreate,
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Add monthly HRA receipt."""
    service = ESSITDeclarationService(session)
    await _get_owned_declaration(service, declaration_id, ess_context.employee_id)

    receipt = await service.add_hra_receipt(declaration_id=declaration_id, **request.model_dump())

    await session.commit()

    return {
        "id": str(receipt.id),
        "month": receipt.month,
        "rent_amount": float(receipt.rent_amount),
        "receipt_uploaded": receipt.receipt_uploaded,
    }


@router.put("/{declaration_id}/home-loan")
async def update_home_loan_details(
    declaration_id: UUID,
    request: HomeLoanDetailsUpdate,
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Update home loan details."""
    service = ESSITDeclarationService(session)
    await _get_owned_declaration(service, declaration_id, ess_context.employee_id)

    try:
        await service.update_home_loan_details(
            declaration_id=declaration_id, **request.model_dump()
        )
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    await session.commit()

    return {"success": True}


# ==================== Submission & Tax Calculation ====================


@router.post("/{declaration_id}/submit")
async def submit_declaration(
    declaration_id: UUID,
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Submit declaration for verification."""
    service = ESSITDeclarationService(session)
    await _get_owned_declaration(service, declaration_id, ess_context.employee_id)

    try:
        declaration = await service.submit_declaration(declaration_id)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    await session.commit()

    return {"success": True, "status": declaration.status.value}


@router.post(
    "/{declaration_id}/calculate-tax",
    response_model=TaxCalculationResponse,
    response_model_by_alias=True,
)
async def calculate_tax(
    declaration_id: UUID,
    request: TaxCalculationRequest,
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Calculate estimated tax liability."""
    service = ESSITDeclarationService(session)
    await _get_owned_declaration(service, declaration_id, ess_context.employee_id)

    try:
        result = await service.calculate_tax_liability(
            declaration_id=declaration_id,
            gross_salary=request.gross_salary,
            other_income=request.other_income,
        )
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")

    await session.commit()

    return TaxCalculationResponse(**result)


# ==================== Attendance Regularization ====================


@router.post("/regularization", response_model=RegularizationResponse, response_model_by_alias=True)
async def create_regularization(
    request: RegularizationCreate,
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Create attendance regularization request."""
    service = ESSITDeclarationService(session)

    reg = await service.create_regularization_request(
        organization_id=ess_context.organization_id,
        employee_id=ess_context.employee_id,
        **request.model_dump(),
    )

    await session.commit()

    return RegularizationResponse(
        id=str(reg.id),
        request_number=reg.request_number,
        attendance_date=reg.attendance_date,
        regularization_type=reg.regularization_type,
        reason=reg.reason,
        status=reg.status,
        approved_by=str(reg.approved_by) if reg.approved_by else None,
        approved_date=reg.approved_date.isoformat() if reg.approved_date else None,
        approver_remarks=reg.approver_remarks,
        created_at=reg.created_at.isoformat(),
    )


@router.get(
    "/regularization", response_model=List[RegularizationResponse], response_model_by_alias=True
)
async def get_regularizations(
    status: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Get regularization requests."""
    service = ESSITDeclarationService(session)

    regs, total = await service.get_regularization_requests(
        employee_id=ess_context.employee_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )

    return [
        RegularizationResponse(
            id=str(r.id),
            request_number=r.request_number,
            attendance_date=r.attendance_date,
            regularization_type=r.regularization_type,
            reason=r.reason,
            status=r.status,
            approved_by=str(r.approved_by) if r.approved_by else None,
            approved_date=r.approved_date.isoformat() if r.approved_date else None,
            approver_remarks=r.approver_remarks,
            created_at=r.created_at.isoformat(),
        )
        for r in regs
    ]


# ==================== Helper Functions ====================


def _format_declaration_detail(declaration) -> DeclarationDetailResponse:
    """Format declaration detail response."""
    return DeclarationDetailResponse(
        id=str(declaration.id),
        financial_year=declaration.financial_year,
        tax_regime=declaration.tax_regime,
        total_declared_amount=float(declaration.total_declared_amount),
        total_verified_amount=float(declaration.total_verified_amount),
        total_approved_amount=float(declaration.total_approved_amount),
        status=declaration.status.value,
        version=declaration.version,
        hra_declared=float(declaration.hra_declared) if declaration.hra_declared else None,
        rent_paid_monthly=(
            float(declaration.rent_paid_monthly) if declaration.rent_paid_monthly else None
        ),
        landlord_name=declaration.landlord_name,
        metro_city=declaration.metro_city,
        home_loan_interest=(
            float(declaration.home_loan_interest) if declaration.home_loan_interest else None
        ),
        home_loan_principal=(
            float(declaration.home_loan_principal) if declaration.home_loan_principal else None
        ),
        property_type=declaration.property_type,
        estimated_taxable_income=(
            float(declaration.estimated_taxable_income)
            if declaration.estimated_taxable_income
            else None
        ),
        estimated_tax_liability=(
            float(declaration.estimated_tax_liability)
            if declaration.estimated_tax_liability
            else None
        ),
        monthly_tds=float(declaration.monthly_tds) if declaration.monthly_tds else None,
        submitted_date=(
            declaration.submitted_date.isoformat() if declaration.submitted_date else None
        ),
        verified_date=declaration.verified_date.isoformat() if declaration.verified_date else None,
        items=[
            DeclarationItemResponse(
                id=str(item.id),
                section_code=item.section_code,
                particular=item.particular,
                declared_amount=float(item.declared_amount),
                verified_amount=float(item.verified_amount) if item.verified_amount else None,
                approved_amount=float(item.approved_amount) if item.approved_amount else None,
                proof_submitted=item.proof_submitted,
                is_verified=item.is_verified,
            )
            for item in declaration.items
        ],
    )
