"""Collateral/Security Management API endpoints."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.base import CamelSchema
from app.services.lending import CollateralService

router = APIRouter()


# Request/Response Schemas
class PropertyDetails(CamelSchema):
    """Property details for collateral."""

    address: str | None = None
    area_sqft: Decimal | None = None
    survey_number: str | None = None
    type: str | None = None
    detailed_description: str | None = None


class OwnerDetails(CamelSchema):
    """Owner details for collateral."""

    name: str | None = None
    relationship: str | None = None
    is_third_party: bool = False
    entity_id: UUID | None = None


class ValuationDetails(CamelSchema):
    """Valuation details for collateral."""

    declared_value: Decimal | None = None
    market_value: Decimal | None = None
    forced_sale_value: Decimal | None = None
    valuation_date: date | None = None
    valuer_name: str | None = None
    valuer_firm: str | None = None
    report_path: str | None = None


class CollateralCreateRequest(CamelSchema):
    """Request to create a collateral."""

    sanction_id: UUID
    security_category: str = Field(..., description="PRIMARY, COLLATERAL, GUARANTEE")
    security_type: str = Field(..., description="IMMOVABLE_PROPERTY, MOVABLE_ASSET, etc.")
    description: str
    acceptable_value: Decimal = Field(..., gt=0)
    margin_percentage: Decimal = Field(default=Decimal("25"), ge=0, le=100)
    charge_type: str = Field(default="FIRST")
    property_details: PropertyDetails | None = None
    owner_details: OwnerDetails | None = None
    valuation_details: ValuationDetails | None = None


class CollateralResponse(CamelSchema):
    """Collateral response."""

    id: UUID
    sanction_id: UUID
    security_number: int
    security_category: str
    security_type: str
    description: str
    acceptable_value: Decimal
    margin_percentage: Decimal
    net_value: Decimal
    status: str


class ValuationUpdateRequest(CamelSchema):
    """Request to update collateral valuation."""

    security_id: UUID
    market_value: Decimal = Field(..., gt=0)
    forced_sale_value: Decimal | None = None
    acceptable_value: Decimal | None = None
    valuation_date: date | None = None
    valuer_name: str | None = None
    valuer_firm: str | None = None
    report_path: str | None = None
    next_valuation_date: date | None = None


class ReleaseRequest(CamelSchema):
    """Request to release collateral."""

    security_id: UUID
    release_reason: str
    release_date: date | None = None
    release_to: str | None = None


class SubstitutionRequest(CamelSchema):
    """Request to substitute collateral."""

    old_security_id: UUID
    new_security: CollateralCreateRequest
    substitution_reason: str


class CoverageResponse(CamelSchema):
    """Security coverage response."""

    sanction_id: UUID
    loan_amount: Decimal
    total_acceptable_value: Decimal
    total_net_value: Decimal
    coverage_ratio: Decimal
    is_fully_secured: bool


class EncumbranceRequest(CamelSchema):
    """Request to add encumbrance."""

    security_id: UUID
    charge_holder: str
    charge_amount: Decimal
    charge_date: date | None = None
    charge_reference: str | None = None


class ChargeCreationRequest(CamelSchema):
    """Request to record charge creation."""

    security_id: UUID
    charge_creation_date: date
    charge_id: str | None = None
    roc_filing_date: date | None = None
    roc_filing_srn: str | None = None
    cersai_registration_date: date | None = None
    cersai_transaction_id: str | None = None


# Endpoints
@router.post("/", response_model=CollateralResponse, response_model_by_alias=True)
async def create_collateral(
    request: CollateralCreateRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Create a new collateral/security."""
    service = CollateralService(db)

    security = await service.create_security(
        sanction_id=request.sanction_id,
        security_category=request.security_category,
        security_type=request.security_type,
        description=request.description,
        acceptable_value=request.acceptable_value,
        margin_percentage=request.margin_percentage,
        charge_type=request.charge_type,
        property_details=request.property_details.dict() if request.property_details else None,
        owner_details=request.owner_details.dict() if request.owner_details else None,
        valuation_details=request.valuation_details.dict() if request.valuation_details else None,
        user_id=current_user.id,
    )

    return CollateralResponse(
        id=security.id,
        sanction_id=security.sanction_id,
        security_number=security.security_number,
        security_category=security.security_category.name,
        security_type=security.security_type.name,
        description=security.description,
        acceptable_value=security.acceptable_value,
        margin_percentage=security.margin_percentage,
        net_value=security.net_value,
        status=(
            security.status.name if hasattr(security, "status") and security.status else "ACTIVE"
        ),
    )


@router.put("/valuation")
async def update_valuation(
    request: ValuationUpdateRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Update collateral valuation."""
    service = CollateralService(db)

    security = await service.update_valuation(
        security_id=request.security_id,
        market_value=request.market_value,
        forced_sale_value=request.forced_sale_value,
        acceptable_value=request.acceptable_value,
        valuation_date=request.valuation_date,
        valuer_name=request.valuer_name,
        valuer_firm=request.valuer_firm,
        report_path=request.report_path,
        next_valuation_date=request.next_valuation_date,
        user_id=current_user.id,
    )

    return {
        "security_id": str(security.id),
        "market_value": security.market_value,
        "acceptable_value": security.acceptable_value,
        "net_value": security.net_value,
        "valuation_date": security.valuation_date,
        "next_valuation_date": security.next_valuation_date,
        "message": "Valuation updated successfully",
    }


@router.post("/release")
async def release_collateral(
    request: ReleaseRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Release a collateral."""
    service = CollateralService(db)

    security = await service.release_security(
        security_id=request.security_id,
        release_reason=request.release_reason,
        release_date=request.release_date,
        release_to=request.release_to,
        user_id=current_user.id,
    )

    return {
        "security_id": str(security.id),
        "status": security.status.name,
        "release_date": security.release_date,
        "message": "Collateral released successfully",
    }


@router.post("/substitute")
async def substitute_collateral(
    request: SubstitutionRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Substitute one collateral with another."""
    service = CollateralService(db)

    new_security_data = {
        "category": request.new_security.security_category,
        "type": request.new_security.security_type,
        "description": request.new_security.description,
        "acceptable_value": request.new_security.acceptable_value,
        "margin_percentage": request.new_security.margin_percentage,
        "charge_type": request.new_security.charge_type,
        "property_details": (
            request.new_security.property_details.dict()
            if request.new_security.property_details
            else None
        ),
        "owner_details": (
            request.new_security.owner_details.dict()
            if request.new_security.owner_details
            else None
        ),
        "valuation_details": (
            request.new_security.valuation_details.dict()
            if request.new_security.valuation_details
            else None
        ),
    }

    result = await service.substitute_security(
        old_security_id=request.old_security_id,
        new_security_data=new_security_data,
        substitution_reason=request.substitution_reason,
        user_id=current_user.id,
    )

    return {
        "old_security_id": str(result["old_security"].id),
        "new_security_id": str(result["new_security"].id),
        "message": "Collateral substituted successfully",
    }


@router.get(
    "/coverage/{sanction_id}",
    response_model=CoverageResponse,
    response_model_by_alias=True,
)
async def get_coverage(
    sanction_id: UUID,
    include_released: bool = Query(default=False),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Get security coverage for a sanction."""
    service = CollateralService(db)

    coverage = await service.get_security_coverage(
        sanction_id=sanction_id,
        include_released=include_released,
    )

    return CoverageResponse(
        sanction_id=sanction_id,
        loan_amount=coverage["loan_amount"],
        total_acceptable_value=coverage["total_acceptable_value"],
        total_net_value=coverage["total_net_value"],
        coverage_ratio=coverage["coverage_ratio"],
        is_fully_secured=coverage["is_fully_secured"],
    )


@router.get("/loan/{loan_account_id}")
async def get_collaterals_by_loan(
    loan_account_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Get collaterals for a loan account."""
    service = CollateralService(db)

    securities = await service.get_securities_by_loan(loan_account_id)

    return {
        "loan_account_id": str(loan_account_id),
        "count": len(securities),
        "securities": [
            {
                "id": str(s.id),
                "security_number": s.security_number,
                "security_category": s.security_category.name,
                "security_type": s.security_type.name,
                "description": s.description,
                "acceptable_value": s.acceptable_value,
                "margin_percentage": s.margin_percentage,
                "net_value": s.net_value,
                "market_value": s.market_value,
                "valuation_date": s.valuation_date,
                "next_valuation_date": s.next_valuation_date,
            }
            for s in securities
        ],
    }


@router.get("/due-valuation")
async def get_collaterals_due_valuation(
    days_ahead: int = Query(default=30, description="Days to look ahead"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get collaterals due for revaluation."""
    service = CollateralService(db)

    securities = await service.get_securities_due_for_valuation(
        organization_id=current_user.organization_id,
        days_ahead=days_ahead,
    )

    return {
        "organization_id": str(current_user.organization_id),
        "count": len(securities),
        "securities": securities,
    }


@router.post("/encumbrance")
async def add_encumbrance(
    request: EncumbranceRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Add existing encumbrance to collateral."""
    service = CollateralService(db)

    security = await service.add_encumbrance(
        security_id=request.security_id,
        charge_holder=request.charge_holder,
        charge_amount=request.charge_amount,
        charge_date=request.charge_date,
        charge_reference=request.charge_reference,
        user_id=current_user.id,
    )

    return {
        "security_id": str(security.id),
        "has_existing_charge": security.has_existing_charge,
        "existing_charge_holder": security.existing_charge_holder,
        "existing_charge_amount": security.existing_charge_amount,
        "message": "Encumbrance recorded successfully",
    }


@router.post("/charge")
async def record_charge_creation(
    request: ChargeCreationRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Record charge creation/registration."""
    service = CollateralService(db)

    security = await service.record_charge_creation(
        security_id=request.security_id,
        charge_creation_date=request.charge_creation_date,
        charge_id=request.charge_id,
        roc_filing_date=request.roc_filing_date,
        roc_filing_srn=request.roc_filing_srn,
        cersai_registration_date=request.cersai_registration_date,
        cersai_transaction_id=request.cersai_transaction_id,
        user_id=current_user.id,
    )

    return {
        "security_id": str(security.id),
        "charge_created": security.charge_created,
        "charge_creation_date": security.charge_creation_date,
        "status": security.status.name,
        "message": "Charge creation recorded successfully",
    }


@router.get("/summary")
async def get_collateral_summary(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get collateral summary for organization."""
    service = CollateralService(db)

    summary = await service.get_collateral_summary(current_user.organization_id)

    return summary
