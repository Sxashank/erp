"""Authentication service."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    verify_password_reset_token,
    verify_password,
    get_password_hash,
    verify_token,
    verify_mfa_code,
)
from app.core.constants import TokenType, UserStatus
from app.core.exceptions import (
    UnauthorizedException,
    BadRequestException,
    AccountLockedException,
    PasswordExpiredException,
)
from app.models.auth.user import User
from app.models.auth.session import UserSession
from app.repositories.auth.user_repo import UserRepository, UserSessionRepository
from app.schemas.auth.token import Token, LoginRequest, UserBasicInfo


class AuthService:
    """Service for authentication operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.session_repo = UserSessionRepository(session)

    async def login(
        self,
        request: LoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[Token, bool]:
        """
        Authenticate user and return tokens.
        Returns (token, requires_mfa).
        """
        # Find user
        user = await self.user_repo.get_by_username_or_email(request.username)
        if not user:
            raise UnauthorizedException("Invalid credentials")

        # Check if account is locked
        if user.is_locked:
            raise AccountLockedException()

        # Check if account is active
        if user.status != UserStatus.ACTIVE.value:
            raise UnauthorizedException("Account is not active")

        # Verify password
        if not verify_password(request.password, user.password_hash):
            # Increment failed attempts
            await self.user_repo.increment_failed_attempts(user)

            # Lock account if too many failed attempts
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                lock_until = datetime.now(timezone.utc) + timedelta(
                    minutes=settings.ACCOUNT_LOCKOUT_MINUTES
                )
                await self.user_repo.lock_account(user, lock_until)
                raise AccountLockedException()

            raise UnauthorizedException("Invalid credentials")

        # Check MFA
        if user.mfa_enabled:
            if not request.otp:
                # Return indication that MFA is required
                return None, True

            if not verify_mfa_code(user.mfa_secret, request.otp):
                raise UnauthorizedException("Invalid OTP code")

        # Check password expiry
        if user.is_password_expired:
            raise PasswordExpiredException()

        # Generate tokens
        token = await self._create_tokens(user, ip_address, user_agent)

        # Update last login
        await self.user_repo.update_last_login(user, ip_address)

        return token, False

    async def refresh_token(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None,
    ) -> Token:
        """Refresh access token using refresh token.

        Replay detection (CLAUDE.md §8.1): if the presented token hash
        maps to a session that has already been revoked for `rotated`,
        that is presumptive replay — we revoke the entire token_family
        and reject the request. See STAGE-5-PENDING-004.
        """
        from app.core.refresh_token_chain import (
            REPLAY_REASON,
            RefreshOutcome,
            classify_refresh,
        )

        # Verify token signature / type / expiry.
        payload = verify_token(refresh_token, TokenType.REFRESH)
        if not payload:
            raise UnauthorizedException("Invalid refresh token")

        token_hash = self._hash_token(refresh_token)

        # Look up INCLUDING revoked so we can catch rotated-then-replayed tokens.
        session = await self.session_repo.get_by_token_hash_including_revoked(token_hash)
        decision = classify_refresh(session)

        if decision.outcome == RefreshOutcome.REPLAY:
            # Kill the entire rotation chain.
            assert session is not None  # classify_refresh returns REPLAY only when session exists
            revoked = await self.session_repo.revoke_token_family(
                session.token_family, reason=REPLAY_REASON
            )
            await self.session.commit()
            raise UnauthorizedException(
                f"Refresh-token replay detected; revoked {revoked} sessions"
            )

        if decision.outcome != RefreshOutcome.VALID or session is None:
            raise UnauthorizedException("Invalid or expired session")

        # Get user
        user = await self.user_repo.get_with_roles(session.user_id)
        if not user or user.status != UserStatus.ACTIVE.value:
            raise UnauthorizedException("User not found or inactive")

        # Update session last used
        session.last_used_at = datetime.now(timezone.utc)

        # Get user permissions
        permissions = await self.user_repo.get_user_permissions(user.id)
        roles = [ur.role.code for ur in user.user_roles if ur.is_valid]

        # Create new access token
        access_token = create_access_token(
            subject=str(user.id),
            additional_claims={
                "roles": roles,
                "permissions": list(permissions),
            },
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,  # Return same refresh token
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserBasicInfo(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                roles=roles,
                permissions=list(permissions),
            ),
        )

    async def logout(self, refresh_token: str) -> bool:
        """Logout user by revoking refresh token."""
        token_hash = self._hash_token(refresh_token)
        session = await self.session_repo.get_by_token_hash(token_hash)

        if session:
            session.revoke("logout")
            await self.session.flush()
            return True
        return False

    async def logout_all(self, user_id: UUID) -> int:
        """Logout user from all sessions."""
        return await self.session_repo.revoke_all_user_sessions(user_id, "logout_all")

    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change user password."""
        user = await self.user_repo.get(user_id)
        if not user:
            raise BadRequestException("User not found")

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise BadRequestException("Current password is incorrect")

        # Update password
        user.password_hash = get_password_hash(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        user.password_expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.PASSWORD_EXPIRY_DAYS
        )
        user.must_change_password = False

        # Revoke all other sessions
        await self.session_repo.revoke_all_user_sessions(user_id, "password_change")

        await self.session.flush()
        return True

    async def forgot_password(self, email: str) -> str:
        """
        Generate password reset token for user.
        Returns the reset token (in production, send via email).
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            # Don't reveal if user exists or not for security
            # But still return a fake token pattern
            return None

        if user.status != UserStatus.ACTIVE.value:
            return None

        # Create password reset token
        reset_token = create_password_reset_token(email)
        return reset_token

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset user password using reset token."""
        # Verify token
        email = verify_password_reset_token(token)
        if not email:
            raise BadRequestException("Invalid or expired reset token")

        # Find user
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise BadRequestException("User not found")

        # Update password
        user.password_hash = get_password_hash(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        user.password_expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.PASSWORD_EXPIRY_DAYS
        )
        user.must_change_password = False

        # Revoke all sessions
        await self.session_repo.revoke_all_user_sessions(user.id, "password_reset")

        await self.session.flush()
        return True

    async def admin_reset_password(
        self,
        user_id: UUID,
        new_password: str,
        must_change: bool = True
    ) -> bool:
        """Admin reset user password."""
        user = await self.user_repo.get(user_id)
        if not user:
            raise BadRequestException("User not found")

        # Update password
        user.password_hash = get_password_hash(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        user.password_expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.PASSWORD_EXPIRY_DAYS
        )
        user.must_change_password = must_change

        # Revoke all sessions
        await self.session_repo.revoke_all_user_sessions(user_id, "admin_reset")

        await self.session.flush()
        return True

    async def unlock_user(self, user_id: UUID) -> bool:
        """Unlock a locked user account."""
        user = await self.user_repo.get(user_id)
        if not user:
            raise BadRequestException("User not found")

        await self.user_repo.unlock_account(user)
        return True

    async def _create_tokens(
        self,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Token:
        """Create access and refresh tokens for user."""
        # Get user permissions and roles
        permissions = await self.user_repo.get_user_permissions(user.id)
        roles = [ur.role.code for ur in user.user_roles if ur.is_valid]

        # Create access token
        access_token = create_access_token(
            subject=str(user.id),
            additional_claims={
                "roles": roles,
                "permissions": list(permissions),
            },
        )

        # Create refresh token
        refresh_token = create_refresh_token(subject=str(user.id))
        token_hash = self._hash_token(refresh_token)

        # Create session
        token_family = secrets.token_urlsafe(16)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        session = UserSession(
            user_id=user.id,
            refresh_token_hash=token_hash,
            token_family=token_family,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        self.session.add(session)
        await self.session.flush()

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserBasicInfo(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                roles=roles,
                permissions=list(permissions),
            ),
        )

    def _hash_token(self, token: str) -> str:
        """Hash a token for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()
