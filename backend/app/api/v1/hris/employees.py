"""API endpoints for Employee management."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db, get_db_with_tenant
from app.core.constants import Permissions
from app.models.auth.user import User
from app.schemas.hris.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeListResponse,
    EmployeeFilters,
    EmployeeDocumentCreate,
    EmployeeDocumentUpdate,
    EmployeeDocumentResponse,
    EmployeeFamilyCreate,
    EmployeeFamilyUpdate,
    EmployeeFamilyResponse,
    EmployeeBankAccountCreate,
    EmployeeBankAccountUpdate,
    EmployeeBankAccountResponse,
    EmployeeEducationCreate,
    EmployeeEducationUpdate,
    EmployeeEducationResponse,
    EmployeeExperienceCreate,
    EmployeeExperienceUpdate,
    EmployeeExperienceResponse,
    EmployeeStatutoryCreate,
    EmployeeStatutoryResponse,
    EmployeeLifecycleEventCreate,
    EmployeeLifecycleEventResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.hris.employee_service import EmployeeService
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter()


# ============================================
# Employee CRUD
# ============================================
@router.get("", response_model=PaginatedResponse[EmployeeListResponse], response_model_by_alias=True)
async def list_employees(
    organization_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    designation_id: Optional[UUID] = None,
    unit_id: Optional[UUID] = None,
    employment_type: Optional[str] = None,
    employment_status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_VIEW)),
):
    """List employees with filters."""
    service = EmployeeService(db)
    filters = EmployeeFilters(
        organization_id=organization_id,
        department_id=department_id,
        designation_id=designation_id,
        unit_id=unit_id,
        employment_type=employment_type,
        employment_status=employment_status,
        search=search,
    )
    employees, total = await service.list(filters, skip, limit)

    items = []
    for emp in employees:
        item = EmployeeListResponse(
            id=emp.id,
            employee_code=emp.employee_code,
            first_name=emp.first_name,
            last_name=emp.last_name,
            display_name=emp.display_name,
            gender=emp.gender,
            personal_mobile=emp.personal_mobile,
            official_email=emp.official_email,
            department_id=emp.department_id,
            department_name=emp.department.name if emp.department else None,
            designation_id=emp.designation_id,
            designation_name=emp.designation.name if emp.designation else None,
            date_of_joining=emp.date_of_joining,
            employment_type=emp.employment_type,
            employment_status=emp.employment_status,
            photo_url=emp.photo_url,
        )
        items.append(item)

    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("", response_model=EmployeeResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_employee(
    data: EmployeeCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_CREATE)),
):
    """Create a new employee."""
    service = EmployeeService(db)

    # Check if employee code already exists
    if data.employee_code:
        existing = await service.get_by_code(data.organization_id, data.employee_code)
        if existing:
            raise BadRequestException(
                detail="Employee code already exists",
                error_code="EMPLOYEE_CODE_ALREADY_EXISTS",
            )

    employee = await service.create(data, current_user.id)
    return await _build_employee_response(service, employee)


@router.get("/{employee_id}", response_model=EmployeeResponse, response_model_by_alias=True)
async def get_employee(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_VIEW)),
):
    """Get employee by ID."""
    service = EmployeeService(db)
    employee = await service.get(employee_id, include_related=True)
    if not employee:
        raise NotFoundException(detail="Employee not found", error_code="EMPLOYEE_NOT_FOUND")
    return await _build_employee_response(service, employee)


@router.put("/{employee_id}", response_model=EmployeeResponse, response_model_by_alias=True)
async def update_employee(
    employee_id: UUID,
    data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Update employee."""
    service = EmployeeService(db)
    employee = await service.update(employee_id, data, current_user.id)
    if not employee:
        raise NotFoundException(detail="Employee not found", error_code="EMPLOYEE_NOT_FOUND")
    return await _build_employee_response(service, employee)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_DELETE)),
):
    """Delete (relieve) employee."""
    service = EmployeeService(db)
    success = await service.delete(employee_id)
    if not success:
        raise NotFoundException(detail="Employee not found", error_code="EMPLOYEE_NOT_FOUND")


# ============================================
# Documents
# ============================================
@router.post("/{employee_id}/documents", response_model=EmployeeDocumentResponse, response_model_by_alias=True)
async def add_document(
    employee_id: UUID,
    data: EmployeeDocumentCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Add document to employee."""
    service = EmployeeService(db)
    doc = await service.add_document(employee_id, data, current_user.id)
    return doc


@router.put("/documents/{document_id}", response_model=EmployeeDocumentResponse, response_model_by_alias=True)
async def update_document(
    document_id: UUID,
    data: EmployeeDocumentUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Update employee document."""
    service = EmployeeService(db)
    doc = await service.update_document(document_id, data, current_user.id)
    if not doc:
        raise NotFoundException(detail="Document not found", error_code="DOCUMENT_NOT_FOUND")
    return doc


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Delete employee document."""
    service = EmployeeService(db)
    success = await service.delete_document(document_id)
    if not success:
        raise NotFoundException(detail="Document not found", error_code="DOCUMENT_NOT_FOUND")


@router.post("/documents/{document_id}/verify", response_model=EmployeeDocumentResponse, response_model_by_alias=True)
async def verify_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Verify employee document."""
    service = EmployeeService(db)
    doc = await service.verify_document(document_id, current_user.id)
    if not doc:
        raise NotFoundException(detail="Document not found", error_code="DOCUMENT_NOT_FOUND")
    return doc


# ============================================
# Family Members
# ============================================
@router.post("/{employee_id}/family", response_model=EmployeeFamilyResponse, response_model_by_alias=True)
async def add_family_member(
    employee_id: UUID,
    data: EmployeeFamilyCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Add family member to employee."""
    service = EmployeeService(db)
    family = await service.add_family_member(employee_id, data, current_user.id)
    return family


@router.put("/family/{family_id}", response_model=EmployeeFamilyResponse, response_model_by_alias=True)
async def update_family_member(
    family_id: UUID,
    data: EmployeeFamilyUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Update family member."""
    service = EmployeeService(db)
    family = await service.update_family_member(family_id, data, current_user.id)
    if not family:
        raise NotFoundException(detail="Family member not found", error_code="FAMILY_MEMBER_NOT_FOUND")
    return family


@router.delete("/family/{family_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family_member(
    family_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Delete family member."""
    service = EmployeeService(db)
    success = await service.delete_family_member(family_id)
    if not success:
        raise NotFoundException(detail="Family member not found", error_code="FAMILY_MEMBER_NOT_FOUND")


# ============================================
# Bank Accounts
# ============================================
@router.post("/{employee_id}/bank-accounts", response_model=EmployeeBankAccountResponse, response_model_by_alias=True)
async def add_bank_account(
    employee_id: UUID,
    data: EmployeeBankAccountCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Add bank account to employee."""
    service = EmployeeService(db)
    bank = await service.add_bank_account(employee_id, data, current_user.id)
    return bank


@router.put("/bank-accounts/{bank_id}", response_model=EmployeeBankAccountResponse, response_model_by_alias=True)
async def update_bank_account(
    bank_id: UUID,
    data: EmployeeBankAccountUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Update bank account."""
    service = EmployeeService(db)
    bank = await service.update_bank_account(bank_id, data, current_user.id)
    if not bank:
        raise NotFoundException(detail="Bank account not found", error_code="BANK_ACCOUNT_NOT_FOUND")
    return bank


@router.delete("/bank-accounts/{bank_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bank_account(
    bank_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Delete bank account."""
    service = EmployeeService(db)
    success = await service.delete_bank_account(bank_id)
    if not success:
        raise NotFoundException(detail="Bank account not found", error_code="BANK_ACCOUNT_NOT_FOUND")


# ============================================
# Education
# ============================================
@router.post("/{employee_id}/education", response_model=EmployeeEducationResponse, response_model_by_alias=True)
async def add_education(
    employee_id: UUID,
    data: EmployeeEducationCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Add education to employee."""
    service = EmployeeService(db)
    edu = await service.add_education(employee_id, data, current_user.id)
    return edu


@router.put("/education/{education_id}", response_model=EmployeeEducationResponse, response_model_by_alias=True)
async def update_education(
    education_id: UUID,
    data: EmployeeEducationUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Update education."""
    service = EmployeeService(db)
    edu = await service.update_education(education_id, data, current_user.id)
    if not edu:
        raise NotFoundException(detail="Education not found", error_code="EDUCATION_NOT_FOUND")
    return edu


@router.delete("/education/{education_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_education(
    education_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Delete education."""
    service = EmployeeService(db)
    success = await service.delete_education(education_id)
    if not success:
        raise NotFoundException(detail="Education not found", error_code="EDUCATION_NOT_FOUND")


# ============================================
# Experience
# ============================================
@router.post("/{employee_id}/experience", response_model=EmployeeExperienceResponse, response_model_by_alias=True)
async def add_experience(
    employee_id: UUID,
    data: EmployeeExperienceCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Add experience to employee."""
    service = EmployeeService(db)
    exp = await service.add_experience(employee_id, data, current_user.id)
    return exp


@router.put("/experience/{experience_id}", response_model=EmployeeExperienceResponse, response_model_by_alias=True)
async def update_experience(
    experience_id: UUID,
    data: EmployeeExperienceUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Update experience."""
    service = EmployeeService(db)
    exp = await service.update_experience(experience_id, data, current_user.id)
    if not exp:
        raise NotFoundException(detail="Experience not found", error_code="EXPERIENCE_NOT_FOUND")
    return exp


@router.delete("/experience/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experience(
    experience_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Delete experience."""
    service = EmployeeService(db)
    success = await service.delete_experience(experience_id)
    if not success:
        raise NotFoundException(detail="Experience not found", error_code="EXPERIENCE_NOT_FOUND")


# ============================================
# Statutory Info
# ============================================
@router.get("/{employee_id}/statutory", response_model=EmployeeStatutoryResponse, response_model_by_alias=True)
async def get_statutory(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_VIEW)),
):
    """Get employee statutory info."""
    service = EmployeeService(db)
    statutory = await service.get_statutory(employee_id)
    if not statutory:
        raise NotFoundException(detail="Statutory info not found", error_code="STATUTORY_INFO_NOT_FOUND")
    return statutory


@router.put("/{employee_id}/statutory", response_model=EmployeeStatutoryResponse, response_model_by_alias=True)
async def upsert_statutory(
    employee_id: UUID,
    data: EmployeeStatutoryCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Create or update statutory info."""
    service = EmployeeService(db)
    statutory = await service.upsert_statutory(employee_id, data, current_user.id)
    return statutory


# ============================================
# Lifecycle Events
# ============================================
@router.get("/{employee_id}/lifecycle", response_model=list[EmployeeLifecycleEventResponse], response_model_by_alias=True)
async def get_lifecycle_events(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_VIEW)),
):
    """Get employee lifecycle events."""
    service = EmployeeService(db)
    events = await service.get_lifecycle_events(employee_id)
    return events


@router.post("/{employee_id}/lifecycle", response_model=EmployeeLifecycleEventResponse, response_model_by_alias=True)
async def add_lifecycle_event(
    employee_id: UUID,
    data: EmployeeLifecycleEventCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_EMPLOYEE_UPDATE)),
):
    """Add lifecycle event to employee."""
    service = EmployeeService(db)
    event = await service.add_lifecycle_event(employee_id, data, current_user.id)
    return event


# ============================================
# Helper Functions
# ============================================
async def _build_employee_response(service: EmployeeService, employee) -> EmployeeResponse:
    """Build full employee response with related data."""
    return EmployeeResponse(
        id=employee.id,
        organization_id=employee.organization_id,
        employee_code=employee.employee_code,
        salutation=employee.salutation,
        first_name=employee.first_name,
        middle_name=employee.middle_name,
        last_name=employee.last_name,
        display_name=employee.display_name,
        gender=employee.gender,
        date_of_birth=employee.date_of_birth,
        blood_group=employee.blood_group,
        marital_status=employee.marital_status,
        nationality=employee.nationality,
        personal_email=employee.personal_email,
        personal_mobile=employee.personal_mobile,
        official_email=employee.official_email,
        official_mobile=employee.official_mobile,
        emergency_contact_name=employee.emergency_contact_name,
        emergency_contact_phone=employee.emergency_contact_phone,
        emergency_contact_relation=employee.emergency_contact_relation,
        current_address=employee.current_address,
        permanent_address=employee.permanent_address,
        is_address_same=employee.is_address_same,
        photo_url=employee.photo_url,
        department_id=employee.department_id,
        designation_id=employee.designation_id,
        reporting_manager_id=employee.reporting_manager_id,
        unit_id=employee.unit_id,
        cost_center_id=employee.cost_center_id,
        date_of_joining=employee.date_of_joining,
        confirmation_date=employee.confirmation_date,
        probation_end_date=employee.probation_end_date,
        date_of_leaving=employee.date_of_leaving,
        employment_type=employee.employment_type,
        employment_status=employee.employment_status,
        notice_period_days=employee.notice_period_days,
        shift_id=employee.shift_id,
        week_off_days=employee.week_off_days,
        user_id=employee.user_id,
        pan_number=employee.pan_number,
        aadhaar_number=employee.aadhaar_number,
        uan_number=employee.uan_number,
        esic_number=employee.esic_number,
        full_name=employee.full_name,
        age=employee.age,
        department_name=employee.department.name if employee.department else None,
        designation_name=employee.designation.name if employee.designation else None,
        unit_name=employee.unit.name if employee.unit else None,
        reporting_manager_name=employee.reporting_manager.full_name if employee.reporting_manager else None,
        shift_name=employee.shift.shift_name if employee.shift else None,
        documents=[EmployeeDocumentResponse.model_validate(d) for d in employee.documents] if employee.documents else None,
        family_members=[EmployeeFamilyResponse.model_validate(f) for f in employee.family_members] if employee.family_members else None,
        bank_accounts=[EmployeeBankAccountResponse.model_validate(b) for b in employee.bank_accounts] if employee.bank_accounts else None,
        education=[EmployeeEducationResponse.model_validate(e) for e in employee.education] if employee.education else None,
        experience=[EmployeeExperienceResponse.model_validate(e) for e in employee.experience] if employee.experience else None,
        statutory_info=EmployeeStatutoryResponse.model_validate(employee.statutory_info) if employee.statutory_info else None,
        lifecycle_events=[EmployeeLifecycleEventResponse.model_validate(e) for e in employee.lifecycle_events] if employee.lifecycle_events else None,
    )
