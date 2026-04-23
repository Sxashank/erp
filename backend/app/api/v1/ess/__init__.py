"""ESS Portal API endpoints.

Provides REST API for Employee Self-Service Portal including:
- Authentication (OTP-based login, sessions)
- Profile (view, update requests)
- Payslip & Salary (download, YTD summary)
- Reimbursement Claims
- Helpdesk Tickets (HR/IT)
- IT Declaration (Tax computation)
- Attendance Regularization
"""

from fastapi import APIRouter

from app.api.v1.ess.auth import router as auth_router
from app.api.v1.ess.profile import router as profile_router
from app.api.v1.ess.reimbursement import router as reimbursement_router
from app.api.v1.ess.helpdesk import router as helpdesk_router
from app.api.v1.ess.it_declaration import router as it_declaration_router

router = APIRouter(prefix="/ess", tags=["ESS Portal"])

router.include_router(auth_router)
router.include_router(profile_router)
router.include_router(reimbursement_router)
router.include_router(helpdesk_router)
router.include_router(it_declaration_router)
