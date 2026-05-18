"""User repository."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.auth.role import Role, RolePermission, UserRole
from app.models.auth.session import UserSession
from app.models.auth.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_username(self, username: str) -> User | None:
        """Get user by username."""
        query = (
            select(User)
            .where(
                and_(
                    User.username == username,
                    User.is_active == True,
                )
            )
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role),
                selectinload(User.organization),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        query = select(User).where(
            and_(
                User.email == email,
                User.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> list[User]:
        """Get users with list response relationships eager loaded."""
        query = select(User).options(
            selectinload(User.organization),
            selectinload(User.default_unit),
            selectinload(User.user_roles).selectinload(UserRole.role),
        )
        if not include_inactive:
            query = query.where(User.is_active == True)
        query = query.order_by(User.username).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().unique().all())

    async def get_by_username_or_email(self, identifier: str) -> User | None:
        """Get user by username or email."""
        query = (
            select(User)
            .where(
                and_(
                    or_(
                        User.username == identifier,
                        User.email == identifier,
                    ),
                    User.is_active == True,
                )
            )
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_roles(self, id: UUID) -> User | None:
        """Get user with roles loaded."""
        query = (
            select(User)
            .where(
                and_(
                    User.id == id,
                    User.is_active == True,
                )
            )
            .options(
                selectinload(User.user_roles)
                .selectinload(UserRole.role)
                .selectinload(Role.role_permissions)
                .selectinload(RolePermission.permission),
                selectinload(User.organization),
                selectinload(User.default_unit),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_permissions(self, user_id: UUID) -> set[str]:
        """Get all permission codes for a user."""
        user = await self.get_with_roles(user_id)
        if not user:
            return set()

        permissions = set()
        now = datetime.now(UTC)

        for user_role in user.user_roles:
            # Check if role assignment is valid
            if user_role.effective_from > now:
                continue
            if user_role.effective_to and user_role.effective_to < now:
                continue

            # Get permissions from role
            for role_perm in user_role.role.role_permissions:
                permissions.add(role_perm.permission.code)

        return permissions

    async def update_last_login(
        self,
        user: User,
        ip_address: str | None = None,
    ) -> User:
        """Update user's last login timestamp."""
        user.last_login_at = datetime.now(UTC)
        user.last_login_ip = ip_address
        user.failed_login_attempts = 0
        await self.session.flush()
        return user

    async def increment_failed_attempts(self, user: User) -> User:
        """Increment failed login attempts."""
        user.failed_login_attempts += 1
        await self.session.flush()
        return user

    async def lock_account(self, user: User, until: datetime) -> User:
        """Lock user account."""
        user.locked_until = until
        await self.session.flush()
        return user

    async def unlock_account(self, user: User) -> User:
        """Unlock user account."""
        user.locked_until = None
        user.failed_login_attempts = 0
        await self.session.flush()
        return user

    async def username_exists(self, username: str, exclude_id: UUID | None = None) -> bool:
        """Check if username already exists."""
        query = select(User.id).where(User.username == username)
        if exclude_id:
            query = query.where(User.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def email_exists(self, email: str, exclude_id: UUID | None = None) -> bool:
        """Check if email already exists."""
        query = select(User.id).where(User.email == email)
        if exclude_id:
            query = query.where(User.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None


class UserSessionRepository(BaseRepository[UserSession]):
    """Repository for UserSession operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(UserSession, session)

    async def get_by_token_hash(self, token_hash: str) -> UserSession | None:
        """Get session by refresh token hash — only non-revoked."""
        query = select(UserSession).where(
            and_(
                UserSession.refresh_token_hash == token_hash,
                UserSession.is_revoked == False,
                UserSession.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_token_hash_including_revoked(self, token_hash: str) -> UserSession | None:
        """Get session by token hash, INCLUDING revoked ones.

        Used for replay detection: when a consumed (rotated) refresh token
        is presented a second time, `get_by_token_hash` (which filters
        `is_revoked=False`) returns None and the replay slips through.
        This variant finds it so the caller can classify + revoke the
        whole family. See CLAUDE.md §8.1 and STAGE-5-PENDING-004.
        """
        query = select(UserSession).where(
            UserSession.refresh_token_hash == token_hash,
            UserSession.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def revoke_token_family(
        self,
        token_family: str,
        reason: str = "replay_detected",
    ) -> int:
        """Revoke every session in a rotation chain.

        Triggered when a consumed refresh token is replayed — the stolen
        token and every descendant must be killed.
        """
        query = select(UserSession).where(
            and_(
                UserSession.token_family == token_family,
                UserSession.is_revoked == False,
            )
        )
        result = await self.session.execute(query)
        sessions = result.scalars().all()
        for sess in sessions:
            sess.revoke(reason)
        await self.session.flush()
        return len(sessions)

    async def revoke_all_user_sessions(
        self,
        user_id: UUID,
        reason: str = "logout_all",
    ) -> int:
        """Revoke all sessions for a user."""
        query = select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_revoked == False,
            )
        )
        result = await self.session.execute(query)
        sessions = result.scalars().all()

        for session in sessions:
            session.revoke(reason)

        await self.session.flush()
        return len(sessions)

    async def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions."""
        now = datetime.now(UTC)
        query = select(UserSession).where(UserSession.expires_at < now)
        result = await self.session.execute(query)
        sessions = result.scalars().all()

        for session in sessions:
            await self.session.delete(session)

        await self.session.flush()
        return len(sessions)
