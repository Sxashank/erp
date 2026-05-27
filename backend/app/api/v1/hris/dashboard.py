"""HRIS dashboard API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_db_with_tenant
from app.core.constants import Permissions
from app.core.exceptions import BadRequestException
from app.models.auth.user import User
from app.schemas.hris.dashboard import HRDashboardResponse
from app.services.hris.dashboard_service import HRDashboardService

router = APIRouter()


def _require_organization_id(current_user: User) -> UUID:
    if not current_user.organization_id:
        raise BadRequestException(
            detail="Current user is not assigned to an organization",
            error_code="ORGANIZATION_CONTEXT_REQUIRED",
        )
    return current_user.organization_id


@router.get("/dashboard", response_model=HRDashboardResponse, response_model_by_alias=True)
async def get_hr_dashboard(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(
        RequirePermissions(
            Permissions.HRIS_EMPLOYEE_VIEW,
            Permissions.HRIS_ATTENDANCE_VIEW,
            Permissions.PAYROLL_RUN_VIEW,
            require_all=False,
        )
    ),
):
    """Return the operational HR dashboard for the active organization."""
    service = HRDashboardService(db)
    return await service.get_dashboard(_require_organization_id(current_user))
