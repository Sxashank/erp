"""IIF (Interest Incentivization Fund) services package.

Five service classes split by aggregate root:

- ``SubventionSchemeService`` — scheme master CRUD.
- ``FundUtilizationCategoryService`` — category master CRUD.
- ``LoanUtilizationService`` — application-level fund-utilization lines.
- ``SubventionEnrollmentService`` — loan↔scheme enrolment + eligibility.
- ``SubventionClaimService`` — period claims + compute + report.

Each service owns its transaction boundary per CLAUDE.md §6.4 — the
route opens ``async with db.begin():`` and the service flushes through
the same session.
"""

from app.services.lending.iif.fund_utilization_category_service import (
    FundUtilizationCategoryService,
)
from app.services.lending.iif.loan_utilization_service import (
    LoanUtilizationService,
)
from app.services.lending.iif.subvention_claim_service import (
    SubventionClaimService,
)
from app.services.lending.iif.subvention_enrollment_service import (
    SubventionEnrollmentService,
)
from app.services.lending.iif.subvention_scheme_service import (
    SubventionSchemeService,
)

__all__ = [
    "SubventionSchemeService",
    "FundUtilizationCategoryService",
    "LoanUtilizationService",
    "SubventionEnrollmentService",
    "SubventionClaimService",
]
