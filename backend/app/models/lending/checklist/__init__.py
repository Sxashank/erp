"""Approval-checklist models package.

Tables that power the customisable per-loan approval checklist:

* ``mst_approval_checklist_template`` — per-org (or platform-default)
  master template applied to a loan application.
* ``mst_approval_checklist_item`` — items belonging to a template.
* ``los_loan_checklist`` — the live checklist attached to one loan
  application; carries the template's items at the time it was applied.
* ``los_loan_checklist_item`` — per-application checklist row with its
  own status / evidence / waiver fields.

Mandatory items must be MET / WAIVED / NOT_APPLICABLE before the
sanction approval gate (``SanctionService.approve_sanction``) lets
the loan through.
"""

from app.models.lending.checklist.loan_checklist import (
    LoanChecklist,
    LoanChecklistItem,
)
from app.models.lending.checklist.template import (
    ApprovalChecklistTemplate,
    ApprovalChecklistTemplateItem,
)

__all__ = [
    "ApprovalChecklistTemplate",
    "ApprovalChecklistTemplateItem",
    "LoanChecklist",
    "LoanChecklistItem",
]
