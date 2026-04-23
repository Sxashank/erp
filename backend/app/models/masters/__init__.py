"""Master data models."""

from app.models.masters.organization import Organization
from app.models.masters.unit import Unit
from app.models.masters.department import Department
from app.models.masters.designation import Designation
from app.models.masters.organization_bank_account import OrganizationBankAccount
from app.models.masters.organization_address import OrganizationAddress

__all__ = [
    "Organization",
    "Unit",
    "Department",
    "Designation",
    "OrganizationBankAccount",
    "OrganizationAddress",
]
