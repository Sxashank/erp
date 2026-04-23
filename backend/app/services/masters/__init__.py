"""Master data services."""

from app.services.masters.organization_service import OrganizationService
from app.services.masters.unit_service import UnitService
from app.services.masters.department_service import DepartmentService
from app.services.masters.designation_service import DesignationService
from app.services.masters.organization_bank_account_service import OrganizationBankAccountService
from app.services.masters.organization_address_service import OrganizationAddressService

__all__ = [
    "OrganizationService",
    "UnitService",
    "DepartmentService",
    "DesignationService",
    "OrganizationBankAccountService",
    "OrganizationAddressService",
]
