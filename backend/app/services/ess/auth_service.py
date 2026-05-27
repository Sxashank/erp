"""ESS Portal Authentication Service."""

import random
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ess.ess_user import ESSUser, ESSSession, ESSDevice, ESSOTP
from app.models.ess.enums import ESSUserStatus
from app.models.hris.employee import Employee
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
)


def _truncate(value: Optional[str], limit: int) -> Optional[str]:
    """Clip external device metadata to the target column width."""
    if value is None:
        return None
    return value[:limit]


class ESSAuthService:
    """Service for ESS Portal authentication."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_ess_user_by_mobile(
        self, mobile: str, organization_id: Optional[UUID] = None
    ) -> Optional[ESSUser]:
        """Get ESS user by mobile number."""
        query = select(ESSUser).where(ESSUser.mobile == mobile)
        if organization_id:
            query = query.where(ESSUser.organization_id == organization_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_ess_user_by_employee(self, employee_id: UUID) -> Optional[ESSUser]:
        """Get ESS user by employee ID."""
        query = select(ESSUser).where(ESSUser.employee_id == employee_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_ess_user_by_id(self, ess_user_id: UUID) -> Optional[ESSUser]:
        """Get ESS user by ID."""
        query = select(ESSUser).where(ESSUser.id == ess_user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_ess_user(
        self,
        organization_id: UUID,
        employee_id: UUID,
        mobile: str,
        email: Optional[str] = None,
    ) -> ESSUser:
        """Create a new ESS user for an employee."""
        ess_user = ESSUser(
            organization_id=organization_id,
            employee_id=employee_id,
            mobile=mobile,
            email=email,
            is_mobile_verified=False,
            is_email_verified=False,
            status=ESSUserStatus.ACTIVE,
        )
        self.session.add(ess_user)
        await self.session.flush()
        return ess_user

    async def send_otp(
        self,
        mobile: str,
        otp_type: str = "LOGIN",
        ess_user_id: Optional[UUID] = None,
        purpose: Optional[str] = None,
    ) -> Tuple[str, datetime]:
        """Generate and send OTP to mobile.

        Returns:
            Tuple of (otp_code, expires_at)
        """
        # Generate 6-digit OTP
        otp_code = f"{random.randint(100000, 999999)}"
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        # Store OTP
        otp = ESSOTP(
            ess_user_id=ess_user_id,
            mobile=mobile,
            otp_code=otp_code,
            otp_type=otp_type,
            purpose=purpose,
            expires_at=expires_at,
            is_used=False,
            attempts=0,
            max_attempts=3,
        )
        self.session.add(otp)
        await self.session.flush()

        # External SMS delivery is release-gated; local/manual flows read the stored OTP.

        return otp_code, expires_at

    async def verify_otp(
        self,
        mobile: str,
        otp_code: str,
        otp_type: str = "LOGIN",
    ) -> Tuple[bool, Optional[str]]:
        """Verify OTP.

        Returns:
            Tuple of (success, error_message)
        """
        # Find the latest unused OTP for this mobile
        query = (
            select(ESSOTP)
            .where(
                and_(
                    ESSOTP.mobile == mobile,
                    ESSOTP.otp_type == otp_type,
                    ESSOTP.is_used == False,
                    ESSOTP.expires_at > datetime.utcnow(),
                )
            )
            .order_by(ESSOTP.created_at.desc())
        )

        result = await self.session.execute(query)
        otp = result.scalar_one_or_none()

        if not otp:
            return False, "OTP expired or not found"

        # Check attempts
        if otp.attempts >= otp.max_attempts:
            return False, "Maximum attempts exceeded"

        # Verify OTP
        if otp.otp_code != otp_code:
            otp.attempts += 1
            await self.session.flush()
            return False, f"Invalid OTP. {otp.max_attempts - otp.attempts} attempts remaining"

        # Mark as used
        otp.is_used = True
        otp.used_at = datetime.utcnow()
        await self.session.flush()

        return True, None

    async def login_with_otp(
        self,
        mobile: str,
        otp_code: str,
        device_info: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[Optional[dict], Optional[str]]:
        """Login user with OTP and create session.

        Returns:
            Tuple of (tokens_dict, error_message)
        """
        # Verify OTP
        success, error = await self.verify_otp(mobile, otp_code, "LOGIN")
        if not success:
            return None, error

        # Get ESS user
        ess_user = await self.get_ess_user_by_mobile(mobile)
        if not ess_user:
            return None, "User not found"

        if ess_user.status != ESSUserStatus.ACTIVE:
            return None, f"Account is {ess_user.status.value.lower()}"

        # Check if account is locked
        if ess_user.locked_until and ess_user.locked_until > datetime.utcnow():
            return None, "Account is temporarily locked"

        # Create tokens
        access_token = create_access_token(
            subject=str(ess_user.id),
            additional_claims={
                "employee_id": str(ess_user.employee_id),
                "organization_id": str(ess_user.organization_id),
            },
        )
        refresh_token = create_refresh_token(subject=str(ess_user.id))

        # Create session
        session = ESSSession(
            ess_user_id=ess_user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            device_type=_truncate(device_info.get("device_type"), 50) if device_info else None,
            device_name=_truncate(device_info.get("device_name"), 200) if device_info else None,
            os_name=_truncate(device_info.get("os_name"), 50) if device_info else None,
            os_version=_truncate(device_info.get("os_version"), 50) if device_info else None,
            browser=_truncate(device_info.get("browser"), 100) if device_info else None,
            app_version=_truncate(device_info.get("app_version"), 20) if device_info else None,
            ip_address=_truncate(ip_address, 50),
            login_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=7),
            last_activity=datetime.utcnow(),
            is_active=True,
        )
        self.session.add(session)

        # Update user
        ess_user.last_login = datetime.utcnow()
        ess_user.last_login_ip = ip_address
        ess_user.login_attempts = 0
        ess_user.is_mobile_verified = True

        await self.session.flush()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {
                "id": str(ess_user.id),
                "employee_id": str(ess_user.employee_id),
                "mobile": ess_user.mobile,
                "email": ess_user.email,
            },
        }, None

    async def refresh_token(
        self,
        refresh_token: str,
    ) -> Tuple[Optional[dict], Optional[str]]:
        """Refresh access token.

        Returns:
            Tuple of (tokens_dict, error_message)
        """
        # Find session by refresh token
        query = select(ESSSession).where(
            and_(
                ESSSession.refresh_token == refresh_token,
                ESSSession.is_active == True,
                ESSSession.expires_at > datetime.utcnow(),
            )
        )
        result = await self.session.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            return None, "Invalid or expired refresh token"

        # Get user
        ess_user = await self.get_ess_user_by_id(session.ess_user_id)
        if not ess_user or ess_user.status != ESSUserStatus.ACTIVE:
            return None, "User not found or inactive"

        # Generate new tokens
        new_access_token = create_access_token(
            subject=str(ess_user.id),
            additional_claims={
                "employee_id": str(ess_user.employee_id),
                "organization_id": str(ess_user.organization_id),
            },
        )
        new_refresh_token = create_refresh_token(subject=str(ess_user.id))

        # Update session
        session.session_token = new_access_token
        session.refresh_token = new_refresh_token
        session.expires_at = datetime.utcnow() + timedelta(days=7)
        session.last_activity = datetime.utcnow()

        await self.session.flush()

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": 3600,
        }, None

    async def logout(self, session_token: str) -> bool:
        """Logout user by invalidating session."""
        query = (
            update(ESSSession)
            .where(ESSSession.session_token == session_token)
            .values(is_active=False)
        )
        await self.session.execute(query)
        await self.session.flush()
        return True

    async def logout_all_sessions(self, ess_user_id: UUID) -> int:
        """Logout all sessions for a user."""
        query = (
            update(ESSSession)
            .where(
                and_(
                    ESSSession.ess_user_id == ess_user_id,
                    ESSSession.is_active == True,
                )
            )
            .values(is_active=False)
        )
        result = await self.session.execute(query)
        await self.session.flush()
        return result.rowcount

    async def get_active_sessions(self, ess_user_id: UUID) -> list[ESSSession]:
        """Get all active sessions for a user."""
        query = (
            select(ESSSession)
            .where(
                and_(
                    ESSSession.ess_user_id == ess_user_id,
                    ESSSession.is_active == True,
                    ESSSession.expires_at > datetime.utcnow(),
                )
            )
            .order_by(ESSSession.last_activity.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def revoke_session(self, ess_user_id: UUID, session_id: UUID) -> bool:
        """Revoke one active session owned by a user."""
        query = (
            update(ESSSession)
            .where(
                and_(
                    ESSSession.id == session_id,
                    ESSSession.ess_user_id == ess_user_id,
                    ESSSession.is_active == True,
                )
            )
            .values(is_active=False)
        )
        result = await self.session.execute(query)
        await self.session.flush()
        return bool(result.rowcount)

    async def register_device(
        self,
        ess_user_id: UUID,
        device_uuid: str,
        device_name: str,
        device_type: str,
        fcm_token: Optional[str] = None,
        **kwargs,
    ) -> ESSDevice:
        """Register a new device for push notifications."""
        # Check if device already exists
        query = select(ESSDevice).where(
            and_(
                ESSDevice.ess_user_id == ess_user_id,
                ESSDevice.device_uuid == device_uuid,
            )
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing device
            existing.device_name = device_name
            existing.fcm_token = fcm_token
            existing.last_used = datetime.utcnow()
            existing.is_active = True
            for key, value in kwargs.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            await self.session.flush()
            return existing

        # Create new device
        device = ESSDevice(
            ess_user_id=ess_user_id,
            device_uuid=device_uuid,
            device_name=device_name,
            device_type=device_type,
            fcm_token=fcm_token,
            is_active=True,
            last_used=datetime.utcnow(),
            **kwargs,
        )
        self.session.add(device)
        await self.session.flush()
        return device

    async def lock_account(
        self,
        ess_user_id: UUID,
        lock_duration_minutes: int = 30,
    ) -> None:
        """Lock account after failed attempts."""
        ess_user = await self.get_ess_user_by_id(ess_user_id)
        if ess_user:
            ess_user.locked_until = datetime.utcnow() + timedelta(minutes=lock_duration_minutes)
            ess_user.status = ESSUserStatus.LOCKED
            await self.session.flush()

    async def unlock_account(self, ess_user_id: UUID) -> None:
        """Unlock a locked account."""
        ess_user = await self.get_ess_user_by_id(ess_user_id)
        if ess_user:
            ess_user.locked_until = None
            ess_user.login_attempts = 0
            ess_user.status = ESSUserStatus.ACTIVE
            await self.session.flush()

    async def update_password(
        self,
        ess_user_id: UUID,
        new_password: str,
    ) -> bool:
        """Update user password."""
        ess_user = await self.get_ess_user_by_id(ess_user_id)
        if not ess_user:
            return False

        ess_user.password_hash = get_password_hash(new_password)
        ess_user.password_changed_at = datetime.utcnow()
        ess_user.must_change_password = False
        await self.session.flush()
        return True

    async def verify_password(
        self,
        ess_user_id: UUID,
        password: str,
    ) -> bool:
        """Verify user password."""
        ess_user = await self.get_ess_user_by_id(ess_user_id)
        if not ess_user or not ess_user.password_hash:
            return False
        return verify_password(password, ess_user.password_hash)
