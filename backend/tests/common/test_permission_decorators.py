"""Permission decorator regression tests."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import ForbiddenException
from app.core.permissions import RequirePermissions, require_permissions


def _user_with_role(role_code: str, permission_codes: list[str] | None = None):
    role_permissions = [
        SimpleNamespace(permission=SimpleNamespace(code=permission_code))
        for permission_code in permission_codes or []
    ]
    return SimpleNamespace(
        id=uuid4(),
        user_roles=[
            SimpleNamespace(
                role=SimpleNamespace(
                    code=role_code,
                    role_permissions=role_permissions,
                )
            )
        ],
    )


@pytest.mark.asyncio
async def test_require_permissions_allows_super_admin_role_without_request():
    @RequirePermissions(["HRIS_EMPLOYEE_VIEW"])
    async def endpoint(current_user):
        return "ok"

    assert await endpoint(current_user=_user_with_role("SUPER_ADMIN")) == "ok"


@pytest.mark.asyncio
async def test_require_permissions_allows_loaded_role_permission_without_request():
    @RequirePermissions(["PAYROLL_RUN_VIEW"])
    async def endpoint(current_user):
        return "ok"

    user = _user_with_role("PAYROLL_ADMIN", ["PAYROLL_RUN_VIEW"])

    assert await endpoint(current_user=user) == "ok"


@pytest.mark.asyncio
async def test_require_permissions_rejects_missing_permission_without_request():
    @RequirePermissions(["PAYROLL_RUN_VIEW"])
    async def endpoint(current_user):
        return "ok"

    with pytest.raises(ForbiddenException):
        await endpoint(current_user=_user_with_role("VIEWER"))


@pytest.mark.asyncio
async def test_legacy_require_permissions_uses_same_resolution_path():
    @require_permissions("ESS_PROFILE_VIEW")
    async def endpoint(current_user):
        return "ok"

    user = _user_with_role("ESS_ADMIN", ["ESS_PROFILE_VIEW"])

    assert await endpoint(current_user=user) == "ok"
