"""Master data schemas."""

from app.schemas.masters.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
)
from app.schemas.masters.unit import (
    UnitCreate,
    UnitUpdate,
    UnitResponse,
    UnitTreeResponse,
)
from app.schemas.masters.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentTreeResponse,
)
from app.schemas.masters.designation import (
    DesignationCreate,
    DesignationUpdate,
    DesignationResponse,
)
from app.schemas.masters.organization_bank_account import (
    OrganizationBankAccountCreate,
    OrganizationBankAccountUpdate,
    OrganizationBankAccountResponse,
)
from app.schemas.masters.organization_address import (
    OrganizationAddressCreate,
    OrganizationAddressUpdate,
    OrganizationAddressResponse,
)

__all__ = [
    # Organization
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    # Unit
    "UnitCreate",
    "UnitUpdate",
    "UnitResponse",
    "UnitTreeResponse",
    # Department
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",
    "DepartmentTreeResponse",
    # Designation
    "DesignationCreate",
    "DesignationUpdate",
    "DesignationResponse",
    # Organization Bank Account
    "OrganizationBankAccountCreate",
    "OrganizationBankAccountUpdate",
    "OrganizationBankAccountResponse",
    # Organization Address
    "OrganizationAddressCreate",
    "OrganizationAddressUpdate",
    "OrganizationAddressResponse",
]
