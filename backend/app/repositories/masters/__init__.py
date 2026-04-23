"""Master data repositories."""

from app.repositories.masters.organization_repo import OrganizationRepository
from app.repositories.masters.unit_repo import UnitRepository
from app.repositories.masters.department_repo import DepartmentRepository
from app.repositories.masters.designation_repo import DesignationRepository
from app.repositories.masters.organization_bank_account_repo import OrganizationBankAccountRepository
from app.repositories.masters.organization_address_repo import OrganizationAddressRepository

__all__ = [
    "OrganizationRepository",
    "UnitRepository",
    "DepartmentRepository",
    "DesignationRepository",
    "OrganizationBankAccountRepository",
    "OrganizationAddressRepository",
]
