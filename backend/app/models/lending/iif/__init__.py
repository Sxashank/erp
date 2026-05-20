"""IIF (Interest Incentivization Fund) models package.

Houses the ORM classes that support the IIF subvention domain under the
Maritime Development Fund. Models follow the existing lending-module
convention: ``BaseModel`` + ``AuditMixin`` + ``SoftDeleteMixin`` +
``VersionedMixin`` via the shared ``app.models.base.BaseModel`` mixin
chain. Money is ``Numeric(18, 2)``; rates are ``Numeric(9, 4)`` per
CLAUDE.md §6.2.

Multi-tenant by ``organization_id`` (CLAUDE.md §3.4). The
``SubventionScheme`` and ``FundUtilizationCategory`` tables permit a
NULL ``organization_id`` so the platform can seed scheme-level reference
data once and have every tenant inherit it.
"""

from app.models.lending.iif.application_utilization import (
    ApplicationUtilization,
)
from app.models.lending.iif.application_funding_source import (
    ApplicationFundingSource,
)
from app.models.lending.iif.application_lender_loan import (
    ApplicationLenderLoan,
)
from app.models.lending.iif.fund_utilization_category import (
    FundUtilizationCategory,
)
from app.models.lending.iif.loan_subvention_enrollment import (
    LoanSubventionEnrollment,
)
from app.models.lending.iif.subvention_claim import SubventionClaim
from app.models.lending.iif.subvention_fund_transaction import (
    SubventionFundTransaction,
)
from app.models.lending.iif.subvention_scheme import SubventionScheme

__all__ = [
    "SubventionScheme",
    "FundUtilizationCategory",
    "ApplicationUtilization",
    "ApplicationFundingSource",
    "ApplicationLenderLoan",
    "LoanSubventionEnrollment",
    "SubventionClaim",
    "SubventionFundTransaction",
]
