from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.security import get_password_hash
from app.models.auth.role import Role, UserRole
from app.models.auth.user import User
from app.services.auth.auth_service import AuthService
from app.schemas.auth.token import LoginRequest


@pytest.mark.asyncio
async def test_login_loads_user_roles_without_lazy_loading(session, test_organization):
    role = Role(
        id=uuid4(),
        code="ADMIN",
        name="Administrator",
        is_system_role=True,
        is_active=True,
    )
    user = User(
        id=uuid4(),
        organization_id=test_organization.id,
        username="roleuser",
        email="roleuser@example.com",
        full_name="Role User",
        password_hash=get_password_hash("ChangeMe123!"),
        status="ACTIVE",
        is_active=True,
    )
    user_role = UserRole(
        user_id=user.id,
        role_id=role.id,
        effective_from=datetime.now(UTC) - timedelta(days=1),
    )

    session.add_all([role, user, user_role])
    await session.commit()

    service = AuthService(session)

    token, requires_mfa = await service.login(
        LoginRequest(username="roleuser", password="ChangeMe123!"),
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    assert requires_mfa is False
    assert token is not None
    assert token.access_token
    assert token.refresh_token
    assert token.user.roles == ["ADMIN"]
