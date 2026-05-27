"""ESS Portal Services package.

This module provides services for the Employee Self-Service Portal including:
- Authentication (OTP-based login, sessions, devices)
- Profile Management (view, update requests)
- Payslip & Salary (download payslips, YTD summary)
- Reimbursement Claims
- Helpdesk Tickets (HR/IT)
- IT Declaration (Tax computation)
- Attendance Regularization
"""

from app.services.ess.auth_service import ESSAuthService
from app.services.ess.profile_service import ESSProfileService
from app.services.ess.reimbursement_service import ESSReimbursementService
from app.services.ess.helpdesk_service import ESSHelpdeskService
from app.services.ess.it_declaration_service import ESSITDeclarationService
from app.services.ess.asset_service import ESSAssetService
from app.services.ess.training_service import ESSTrainingService

__all__ = [
    "ESSAuthService",
    "ESSProfileService",
    "ESSReimbursementService",
    "ESSHelpdeskService",
    "ESSITDeclarationService",
    "ESSAssetService",
    "ESSTrainingService",
]
