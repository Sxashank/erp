"""Vendor Portal Authentication Service."""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from app.repositories.vendor_portal.portal_vendor_user_repo import (
    PortalVendorUserRepository,
    PortalVendorSessionRepository,
    PortalVendorOTPRepository,
)
from app.models.vendor_portal.portal_vendor_user import (
    PortalVendorUser,
    PortalVendorSession,
    PortalVendorOTP,
)
from app.models.vendor_portal.enums import (
    VendorPortalUserStatus,
    VendorOTPPurpose,
)
from app.schemas.vendor_portal.auth import (
    VendorLoginRequest,
    VendorLoginResponse,
    VendorOTPRequest,
    VendorUserProfile,
)


class VendorPortalAuthService:
    """Service for vendor portal authentication."""

    OTP_EXPIRY_MINUTES = 10
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_MINUTES = 30
    SESSION_EXPIRY_HOURS = 24
    REFRESH_TOKEN_EXPIRY_DAYS = 7

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = PortalVendorUserRepository(session)
        self.session_repo = PortalVendorSessionRepository(session)
        self.otp_repo = PortalVendorOTPRepository(session)

    async def login_with_password(
        self,
        email: str,
        password: str,
        ip_address: str,
        device_type: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> Tuple[PortalVendorSession, PortalVendorUser]:
        """Login with email and password."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UnauthorizedException("Invalid email or password")

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise UnauthorizedException(
                f"Account is locked. Try again after {user.locked_until}"
            )

        # Check if account is active
        if user.status != VendorPortalUserStatus.ACTIVE:
            raise UnauthorizedException(f"Account is {user.status.value.lower()}")

        # Verify password
        if not user.password_hash or not verify_password(password, user.password_hash):
            await self.user_repo.increment_failed_login(user.id)

            # Lock account if max attempts exceeded
            if user.failed_login_attempts + 1 >= self.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=self.LOCKOUT_MINUTES
                )
                await self.session.flush()

            raise UnauthorizedException("Invalid email or password")

        # Reset failed attempts and update last login
        await self.user_repo.reset_failed_login(user.id)
        await self.user_repo.update_last_login(user.id, ip_address, device_type)

        # Create session
        session = await self._create_session(user.id, ip_address, device_type)

        return session, user

    async def login_with_otp(
        self,
        email: str,
        otp: str,
        ip_address: str,
        device_type: Optional[str] = None,
    ) -> Tuple[PortalVendorSession, PortalVendorUser]:
        """Login with OTP."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UnauthorizedException("Invalid email")

        if user.status != VendorPortalUserStatus.ACTIVE:
            raise UnauthorizedException(f"Account is {user.status.value.lower()}")

        # Verify OTP
        await self._verify_otp(email, otp, VendorOTPPurpose.LOGIN)

        # Update last login
        await self.user_repo.update_last_login(user.id, ip_address, device_type)

        # Create session
        session = await self._create_session(user.id, ip_address, device_type)

        return session, user

    async def generate_otp(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        purpose: VendorOTPPurpose = VendorOTPPurpose.LOGIN,
        organization_id: Optional[UUID] = None,
    ) -> str:
        """Generate and send OTP."""
        if not email and not phone:
            raise ValidationException("Email or phone is required")

        # Verify user exists for login OTP
        if purpose == VendorOTPPurpose.LOGIN:
            if email:
                user = await self.user_repo.get_by_email(email, organization_id)
            else:
                user = await self.user_repo.get_by_phone(phone, organization_id)

            if not user:
                raise NotFoundException("User not found")

            organization_id = user.organization_id

        # Invalidate previous OTPs
        await self.otp_repo.invalidate_previous(email, phone, purpose)

        # Generate OTP
        otp_code = self._generate_otp_code()
        otp_hash = self._hash_otp(otp_code)

        # Create OTP record
        otp = PortalVendorOTP(
            organization_id=organization_id,
            email=email,
            phone=phone,
            otp_code=otp_code,
            otp_hash=otp_hash,
            purpose=purpose,
            expires_at=datetime.utcnow() + timedelta(minutes=self.OTP_EXPIRY_MINUTES),
        )
        self.session.add(otp)
        await self.session.flush()

        # TODO: Send OTP via email/SMS integration

        return otp_code

    async def verify_otp(
        self,
        email: Optional[str],
        phone: Optional[str],
        otp: str,
        purpose: VendorOTPPurpose,
    ) -> bool:
        """Verify OTP."""
        return await self._verify_otp(
            email=email, otp=otp, purpose=purpose, phone=phone
        )

    async def refresh_token(
        self,
        refresh_token: str,
    ) -> Tuple[str, str]:
        """Refresh access token."""
        session = await self.session_repo.get_by_refresh_token(refresh_token)
        if not session:
            raise UnauthorizedException("Invalid refresh token")

        if session.expires_at < datetime.utcnow():
            raise UnauthorizedException("Session expired")

        # Generate new tokens
        access_token = create_access_token(
            subject=str(session.user_id),
            expires_delta=timedelta(hours=self.SESSION_EXPIRY_HOURS),
        )
        new_refresh_token = create_refresh_token(
            subject=str(session.user_id),
            expires_delta=timedelta(days=self.REFRESH_TOKEN_EXPIRY_DAYS),
        )

        # Update session
        session.session_token = access_token
        session.refresh_token = new_refresh_token
        session.last_activity_at = datetime.utcnow()
        await self.session.flush()

        return access_token, new_refresh_token

    async def logout(
        self,
        session_id: UUID,
        reason: str = "user_logout",
    ) -> None:
        """Logout and invalidate session."""
        await self.session_repo.invalidate_session(session_id, reason)
        await self.session.commit()

    async def logout_all_sessions(
        self,
        user_id: UUID,
        reason: str = "security",
    ) -> int:
        """Logout all sessions for a user."""
        count = await self.session_repo.invalidate_all_sessions(user_id, reason)
        await self.session.commit()
        return count

    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change user password."""
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException("User not found")

        if user.password_hash and not verify_password(current_password, user.password_hash):
            raise ValidationException("Current password is incorrect")

        user.password_hash = get_password_hash(new_password)
        user.password_changed_at = datetime.utcnow()
        await self.session.commit()

    async def reset_password(
        self,
        email: str,
        otp: str,
        new_password: str,
    ) -> None:
        """Reset password using OTP."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise NotFoundException("User not found")

        # Verify OTP
        await self._verify_otp(email, otp, VendorOTPPurpose.PASSWORD_RESET)

        # Set new password
        user.password_hash = get_password_hash(new_password)
        user.password_changed_at = datetime.utcnow()
        user.failed_login_attempts = 0
        user.locked_until = None

        # Invalidate all sessions
        await self.session_repo.invalidate_all_sessions(user.id, "password_reset")

        await self.session.commit()

    async def get_current_user(
        self,
        user_id: UUID,
    ) -> PortalVendorUser:
        """Get current user profile."""
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException("User not found")
        return user

    async def validate_session(
        self,
        session_token: str,
    ) -> Optional[PortalVendorSession]:
        """Validate session token."""
        session = await self.session_repo.get_by_token(session_token)
        if not session:
            return None

        if session.expires_at < datetime.utcnow():
            await self.session_repo.invalidate_session(session.id, "expired")
            return None

        # Update last activity
        session.last_activity_at = datetime.utcnow()
        await self.session.flush()

        return session

    # Private methods
    async def _create_session(
        self,
        user_id: UUID,
        ip_address: str,
        device_type: Optional[str] = None,
    ) -> PortalVendorSession:
        """Create a new session."""
        access_token = create_access_token(
            subject=str(user_id),
            expires_delta=timedelta(hours=self.SESSION_EXPIRY_HOURS),
        )
        refresh_token = create_refresh_token(
            subject=str(user_id),
            expires_delta=timedelta(days=self.REFRESH_TOKEN_EXPIRY_DAYS),
        )

        session = PortalVendorSession(
            user_id=user_id,
            session_token=access_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            device_type=device_type,
            expires_at=datetime.utcnow() + timedelta(days=self.REFRESH_TOKEN_EXPIRY_DAYS),
        )
        self.session.add(session)
        await self.session.flush()
        await self.session.refresh(session)

        return session

    async def _verify_otp(
        self,
        email: Optional[str],
        otp: str,
        purpose: VendorOTPPurpose,
        phone: Optional[str] = None,
    ) -> bool:
        """Verify OTP and mark as used."""
        otp_record = await self.otp_repo.get_latest_otp(email, phone, purpose)
        if not otp_record:
            raise ValidationException("OTP not found or expired")

        # Check attempts
        if otp_record.attempts >= otp_record.max_attempts:
            raise ValidationException("Maximum verification attempts exceeded")

        # Verify OTP hash
        if self._hash_otp(otp) != otp_record.otp_hash:
            await self.otp_repo.increment_attempts(otp_record.id)
            raise ValidationException("Invalid OTP")

        # Mark as used
        await self.otp_repo.mark_used(otp_record.id)

        return True

    def _generate_otp_code(self, length: int = 6) -> str:
        """Generate random OTP code."""
        return "".join([str(secrets.randbelow(10)) for _ in range(length)])

    def _hash_otp(self, otp: str) -> str:
        """Hash OTP for secure storage."""
        return hashlib.sha256(otp.encode()).hexdigest()
