"""
Payroll API Router

Aggregates all payroll-related routes.
"""

from fastapi import APIRouter

from app.api.v1.payroll.salary import router as salary_router
from app.api.v1.payroll.payroll import router as payroll_router

router = APIRouter()

# Mount salary routes (components, structures, employee salaries)
router.include_router(salary_router, tags=["Payroll - Salary"])

# Mount payroll routes (statutory, batches, payslips)
router.include_router(payroll_router, tags=["Payroll"])
