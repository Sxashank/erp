"""
Payroll Schemas

Pydantic models for payroll processing operations.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============== Statutory Setup ==============

class StatutorySetupBase(BaseModel):
    """Base schema for statutory setup"""
    statutory_type: str = Field(..., description="PF, ESI, PT, LWF")

    # PF Settings
    pf_employer_rate: Optional[Decimal] = None
    pf_employee_rate: Optional[Decimal] = None
    pf_admin_charge_rate: Optional[Decimal] = None
    pf_edli_rate: Optional[Decimal] = None
    pf_wage_ceiling: Optional[Decimal] = None
    eps_employer_rate: Optional[Decimal] = None
    eps_wage_ceiling: Optional[Decimal] = None

    # ESI Settings
    esi_employer_rate: Optional[Decimal] = None
    esi_employee_rate: Optional[Decimal] = None
    esi_wage_ceiling: Optional[Decimal] = None

    # PT Settings
    pt_state: Optional[str] = None
    pt_slabs: Optional[dict] = None

    # LWF Settings
    lwf_employer_contribution: Optional[Decimal] = None
    lwf_employee_contribution: Optional[Decimal] = None
    lwf_frequency: Optional[str] = None

    effective_from: date
    effective_to: Optional[date] = None
    is_active: bool = True


class StatutorySetupCreate(StatutorySetupBase):
    """Schema for creating statutory setup"""
    organization_id: UUID


class StatutorySetupUpdate(BaseModel):
    """Schema for updating statutory setup"""
    pf_employer_rate: Optional[Decimal] = None
    pf_employee_rate: Optional[Decimal] = None
    pf_admin_charge_rate: Optional[Decimal] = None
    pf_edli_rate: Optional[Decimal] = None
    pf_wage_ceiling: Optional[Decimal] = None
    eps_employer_rate: Optional[Decimal] = None
    eps_wage_ceiling: Optional[Decimal] = None
    esi_employer_rate: Optional[Decimal] = None
    esi_employee_rate: Optional[Decimal] = None
    esi_wage_ceiling: Optional[Decimal] = None
    pt_state: Optional[str] = None
    pt_slabs: Optional[dict] = None
    lwf_employer_contribution: Optional[Decimal] = None
    lwf_employee_contribution: Optional[Decimal] = None
    lwf_frequency: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None


class StatutorySetupResponse(StatutorySetupBase):
    """Schema for statutory setup response"""
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True


# ============== Payroll Batch ==============

class PayrollBatchBase(BaseModel):
    """Base schema for payroll batch"""
    payroll_month: int = Field(..., ge=1, le=12)
    payroll_year: int = Field(..., ge=2000, le=2100)
    pay_period_from: date
    pay_period_to: date
    payment_date: Optional[date] = None
    remarks: Optional[str] = None


class PayrollBatchCreate(PayrollBatchBase):
    """Schema for creating payroll batch"""
    organization_id: UUID


class PayrollBatchUpdate(BaseModel):
    """Schema for updating payroll batch"""
    pay_period_from: Optional[date] = None
    pay_period_to: Optional[date] = None
    payment_date: Optional[date] = None
    remarks: Optional[str] = None


class PayrollBatchResponse(PayrollBatchBase):
    """Schema for payroll batch response"""
    id: UUID
    organization_id: UUID
    batch_number: str
    status: str

    total_employees: int
    total_gross: Decimal
    total_deductions: Decimal
    total_net: Decimal
    total_employer_statutory: Decimal

    total_pf_employee: Decimal
    total_pf_employer: Decimal
    total_esi_employee: Decimal
    total_esi_employer: Decimal
    total_pt: Decimal
    total_tds: Decimal

    processed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PayrollBatchList(BaseModel):
    """Minimal schema for listing"""
    id: UUID
    batch_number: str
    payroll_month: int
    payroll_year: int
    total_employees: int
    total_net: Decimal
    status: str

    class Config:
        from_attributes = True


class PayrollProcessRequest(BaseModel):
    """Request schema for processing payroll"""
    batch_id: UUID
    employee_ids: Optional[List[UUID]] = None  # If None, process all


class PayrollApproveRequest(BaseModel):
    """Request schema for approving payroll"""
    remarks: Optional[str] = None


# ============== Payslip ==============

class PayslipComponentResponse(BaseModel):
    """Schema for payslip component response"""
    id: UUID
    component_code: str
    component_name: str
    component_type: str
    standard_amount: Decimal
    actual_amount: Decimal
    arrears_amount: Decimal
    is_taxable: bool
    taxable_amount: Decimal
    display_order: int

    class Config:
        from_attributes = True


class PayrollStatutoryResponse(BaseModel):
    """Schema for payroll statutory response"""
    id: UUID
    statutory_type: str
    wage_base: Decimal
    employee_rate: Optional[Decimal]
    employee_amount: Decimal
    employer_rate: Optional[Decimal]
    employer_amount: Decimal
    eps_amount: Decimal
    edli_amount: Decimal
    admin_charges: Decimal
    total_amount: Decimal

    class Config:
        from_attributes = True


class PayslipBase(BaseModel):
    """Base schema for payslip"""
    working_days: Decimal
    days_present: Decimal
    days_absent: Decimal
    leave_days: Decimal
    lop_days: Decimal
    overtime_hours: Decimal


class PayslipResponse(PayslipBase):
    """Schema for payslip response"""
    id: UUID
    batch_id: UUID
    employee_id: UUID
    payslip_number: str

    # Employee snapshot
    employee_code: str
    employee_name: str
    department_name: Optional[str]
    designation_name: Optional[str]
    pan_number: Optional[str]
    uan_number: Optional[str]
    esi_number: Optional[str]
    bank_account_number: Optional[str]
    bank_ifsc: Optional[str]

    # Salary figures
    gross_salary: Decimal
    total_earnings: Decimal
    total_deductions: Decimal
    net_salary: Decimal

    # Statutory wages
    pf_wage: Decimal
    esi_wage: Decimal
    pt_wage: Decimal
    taxable_income: Decimal

    # Employer contributions
    employer_pf: Decimal
    employer_esi: Decimal

    # Arrears
    arrears_amount: Decimal
    arrears_remarks: Optional[str]

    status: str
    payment_mode: str
    payment_reference: Optional[str]
    paid_at: Optional[datetime]

    components: List[PayslipComponentResponse] = []
    statutory: List[PayrollStatutoryResponse] = []

    class Config:
        from_attributes = True


class PayslipList(BaseModel):
    """Minimal schema for listing"""
    id: UUID
    payslip_number: str
    employee_code: str
    employee_name: str
    gross_salary: Decimal
    total_deductions: Decimal
    net_salary: Decimal
    status: str

    class Config:
        from_attributes = True


class PayslipUpdate(BaseModel):
    """Schema for updating payslip (manual adjustments)"""
    working_days: Optional[Decimal] = None
    days_present: Optional[Decimal] = None
    days_absent: Optional[Decimal] = None
    leave_days: Optional[Decimal] = None
    lop_days: Optional[Decimal] = None
    overtime_hours: Optional[Decimal] = None
    arrears_amount: Optional[Decimal] = None
    arrears_remarks: Optional[str] = None
    remarks: Optional[str] = None


class PayslipGeneratePDF(BaseModel):
    """Request for generating payslip PDF"""
    payslip_id: UUID
    include_employer_contribution: bool = False
