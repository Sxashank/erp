"""
Salary Component Schemas

Pydantic models for salary component operations.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field
from app.schemas.base import CamelSchema


# ============== Salary Component ==============

class SalaryComponentBase(CamelSchema):
    """Base schema for salary component"""
    component_code: str = Field(..., min_length=1, max_length=20)
    component_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

    component_type: str = Field(..., description="EARNING or DEDUCTION")
    category: str = Field(default="OTHER")

    calculation_type: str = Field(default="FIXED")
    default_value: Optional[Decimal] = None
    formula: Optional[str] = None

    is_taxable: bool = True
    tax_exemption_limit: Optional[Decimal] = None
    exemption_section: Optional[str] = None

    is_part_of_basic: bool = False
    is_part_of_gross: bool = True
    is_part_of_ctc: bool = True
    affects_pf: bool = False
    affects_esi: bool = False
    affects_pt: bool = False
    affects_gratuity: bool = False

    display_order: int = 0
    show_on_payslip: bool = True
    is_active: bool = True


class SalaryComponentCreate(SalaryComponentBase):
    """Schema for creating salary component"""
    organization_id: UUID


class SalaryComponentUpdate(CamelSchema):
    """Schema for updating salary component"""
    component_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    calculation_type: Optional[str] = None
    default_value: Optional[Decimal] = None
    formula: Optional[str] = None
    is_taxable: Optional[bool] = None
    tax_exemption_limit: Optional[Decimal] = None
    exemption_section: Optional[str] = None
    is_part_of_basic: Optional[bool] = None
    is_part_of_gross: Optional[bool] = None
    is_part_of_ctc: Optional[bool] = None
    affects_pf: Optional[bool] = None
    affects_esi: Optional[bool] = None
    affects_pt: Optional[bool] = None
    affects_gratuity: Optional[bool] = None
    display_order: Optional[int] = None
    show_on_payslip: Optional[bool] = None
    is_active: Optional[bool] = None


class SalaryComponentResponse(SalaryComponentBase):
    """Schema for salary component response"""
    id: UUID
    organization_id: UUID


class SalaryComponentList(CamelSchema):
    """Minimal schema for listing"""
    id: UUID
    component_code: str
    component_name: str
    component_type: str
    category: str
    calculation_type: str
    default_value: Optional[Decimal]
    is_active: bool


# ============== Salary Structure ==============

class SalaryStructureComponentBase(CamelSchema):
    """Base schema for structure component"""
    component_id: UUID
    calculation_type: str
    value: Optional[Decimal] = None
    formula: Optional[str] = None
    is_mandatory: bool = True


class SalaryStructureComponentCreate(SalaryStructureComponentBase):
    """Schema for creating structure component"""
    pass


class SalaryStructureComponentResponse(SalaryStructureComponentBase):
    """Schema for structure component response"""
    id: UUID
    component_code: Optional[str] = None
    component_name: Optional[str] = None
    component_type: Optional[str] = None


class SalaryStructureBase(CamelSchema):
    """Base schema for salary structure"""
    structure_code: str = Field(..., min_length=1, max_length=20)
    structure_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

    effective_from: date
    effective_to: Optional[date] = None

    payment_mode: str = "BANK"
    pay_frequency: str = "MONTHLY"
    is_active: bool = True


class SalaryStructureCreate(SalaryStructureBase):
    """Schema for creating salary structure"""
    organization_id: UUID
    components: List[SalaryStructureComponentCreate] = []


class SalaryStructureUpdate(CamelSchema):
    """Schema for updating salary structure"""
    structure_name: Optional[str] = None
    description: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    payment_mode: Optional[str] = None
    pay_frequency: Optional[str] = None
    is_active: Optional[bool] = None
    components: Optional[List[SalaryStructureComponentCreate]] = None


class SalaryStructureResponse(SalaryStructureBase):
    """Schema for salary structure response"""
    id: UUID
    organization_id: UUID
    components: List[SalaryStructureComponentResponse] = []


class SalaryStructureList(CamelSchema):
    """Minimal schema for listing"""
    id: UUID
    structure_code: str
    structure_name: str
    effective_from: date
    effective_to: Optional[date]
    is_active: bool


# ============== Employee Salary ==============

class EmployeeSalaryComponentCreate(CamelSchema):
    """Schema for employee salary component"""
    component_id: UUID
    monthly_amount: Decimal
    annual_amount: Decimal
    is_overridden: bool = False


class EmployeeSalaryComponentResponse(CamelSchema):
    """Schema for employee salary component response"""
    id: UUID
    component_id: UUID
    component_code: Optional[str] = None
    component_name: Optional[str] = None
    component_type: Optional[str] = None
    monthly_amount: Decimal
    annual_amount: Decimal
    is_overridden: bool


class EmployeeSalaryBase(CamelSchema):
    """Base schema for employee salary"""
    structure_id: UUID
    effective_from: date
    effective_to: Optional[date] = None

    annual_ctc: Decimal
    annual_gross: Decimal
    annual_net: Optional[Decimal] = None

    monthly_ctc: Decimal
    monthly_gross: Decimal
    monthly_basic: Decimal
    monthly_net: Optional[Decimal] = None

    revision_reason: Optional[str] = None


class EmployeeSalaryCreate(EmployeeSalaryBase):
    """Schema for creating employee salary"""
    employee_id: UUID
    components: List[EmployeeSalaryComponentCreate] = []


class EmployeeSalaryUpdate(CamelSchema):
    """Schema for updating employee salary"""
    structure_id: Optional[UUID] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    annual_ctc: Optional[Decimal] = None
    annual_gross: Optional[Decimal] = None
    annual_net: Optional[Decimal] = None
    monthly_ctc: Optional[Decimal] = None
    monthly_gross: Optional[Decimal] = None
    monthly_basic: Optional[Decimal] = None
    monthly_net: Optional[Decimal] = None
    revision_reason: Optional[str] = None
    components: Optional[List[EmployeeSalaryComponentCreate]] = None


class EmployeeSalaryResponse(EmployeeSalaryBase):
    """Schema for employee salary response"""
    id: UUID
    employee_id: UUID
    revision_number: int
    status: str
    components: List[EmployeeSalaryComponentResponse] = []

    # Snapshot fields
    employee_code: Optional[str] = None
    employee_name: Optional[str] = None
    structure_code: Optional[str] = None
    structure_name: Optional[str] = None


class EmployeeSalaryList(CamelSchema):
    """Minimal schema for listing"""
    id: UUID
    employee_id: UUID
    employee_code: Optional[str] = None
    employee_name: Optional[str] = None
    structure_name: Optional[str] = None
    effective_from: date
    annual_ctc: Decimal
    monthly_gross: Decimal
    status: str

