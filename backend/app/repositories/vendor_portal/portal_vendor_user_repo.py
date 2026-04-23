"""Vendor Portal User Repositories."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.vendor_portal.portal_vendor_user import (
    PortalVendorUser,
    PortalVendorSession,
    PortalVendorOTP,
)
from app.models.vendor_portal.enums import VendorPortalUserStatus, VendorOTPPurpose


class PortalVendorUserRepository(BaseRepository[PortalVendorUser]):
    """Repository for vendor portal user operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(PortalVendorUser, session)

    async def get_by_email(
        self, email: str, organization_id: Optional[UUID] = None
    ) -> Optional[PortalVendorUser]:
        """Get user by email."""
        query = select(self.model).where(
            and_(
                self.model.email == email,
                self.model.is_active == True,
            )
        )
        if organization_id:
            query = query.where(self.model.organization_id == organization_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_vendor(
        self, vendor_id: UUID, include_inactive: bool = False
    ) -> List[PortalVendorUser]:
        """Get all portal users for a vendor."""
        query = select(self.model).where(self.model.vendor_id == vendor_id)
        if not include_inactive:
            query = query.where(self.model.is_active == True)
        query = query.order_by(self.model.is_primary_contact.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_primary_contact(self, vendor_id: UUID) -> Optional[PortalVendorUser]:
        """Get primary contact for a vendor."""
        query = select(self.model).where(
            and_(
                self.model.vendor_id == vendor_id,
                self.model.is_primary_contact == True,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_phone(
        self, phone: str, organization_id: Optional[UUID] = None
    ) -> Optional[PortalVendorUser]:
        """Get user by phone number."""
        query = select(self.model).where(
            and_(
                self.model.phone == phone,
                self.model.is_active == True,
            )
        )
        if organization_id:
            query = query.where(self.model.organization_id == organization_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def increment_failed_login(self, user_id: UUID) -> None:
        """Increment failed login attempts."""
        user = await self.get(user_id)
        if user:
            user.failed_login_attempts += 1
            await self.session.flush()

    async def reset_failed_login(self, user_id: UUID) -> None:
        """Reset failed login attempts."""
        user = await self.get(user_id)
        if user:
            user.failed_login_attempts = 0
            user.locked_until = None
            await self.session.flush()

    async def update_last_login(
        self, user_id: UUID, ip_address: str, device: Optional[str] = None
    ) -> None:
        """Update last login info."""
        user = await self.get(user_id)
        if user:
            user.last_login_at = datetime.utcnow()
            user.last_login_ip = ip_address
            user.last_login_device = device
            user.login_count += 1
            await self.session.flush()


class PortalVendorSessionRepository(BaseRepository[PortalVendorSession]):
    """Repository for vendor portal session operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(PortalVendorSession, session)

    async def get_by_token(self, token: str) -> Optional[PortalVendorSession]:
        """Get session by token."""
        query = select(self.model).where(
            and_(
                self.model.session_token == token,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_refresh_token(self, token: str) -> Optional[PortalVendorSession]:
        """Get session by refresh token."""
        query = select(self.model).where(
            and_(
                self.model.refresh_token == token,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_sessions(self, user_id: UUID) -> List[PortalVendorSession]:
        """Get all active sessions for a user."""
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.is_active == True,
                self.model.expires_at > datetime.utcnow(),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def invalidate_session(
        self, session_id: UUID, reason: str = "logout"
    ) -> None:
        """Invalidate a session."""
        session = await self.get(session_id)
        if session:
            session.is_active = False
            session.logout_at = datetime.utcnow()
            session.logout_reason = reason
            await self.session.flush()

    async def invalidate_all_sessions(self, user_id: UUID, reason: str) -> int:
        """Invalidate all sessions for a user."""
        sessions = await self.get_active_sessions(user_id)
        for session in sessions:
            session.is_active = False
            session.logout_at = datetime.utcnow()
            session.logout_reason = reason
        await self.session.flush()
        return len(sessions)


class PortalVendorOTPRepository(BaseRepository[PortalVendorOTP]):
    """Repository for vendor portal OTP operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(PortalVendorOTP, session)

    async def get_latest_otp(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        purpose: VendorOTPPurpose = VendorOTPPurpose.LOGIN,
    ) -> Optional[PortalVendorOTP]:
        """Get latest unused OTP."""
        conditions = [
            self.model.purpose == purpose,
            self.model.is_used == False,
            self.model.expires_at > datetime.utcnow(),
        ]
        if email:
            conditions.append(self.model.email == email)
        if phone:
            conditions.append(self.model.phone == phone)

        query = (
            select(self.model)
            .where(and_(*conditions))
            .order_by(self.model.generated_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def mark_used(self, otp_id: UUID) -> None:
        """Mark OTP as used."""
        otp = await self.get(otp_id)
        if otp:
            otp.is_used = True
            otp.verified_at = datetime.utcnow()
            await self.session.flush()

    async def increment_attempts(self, otp_id: UUID) -> int:
        """Increment OTP verification attempts."""
        otp = await self.get(otp_id)
        if otp:
            otp.attempts += 1
            await self.session.flush()
            return otp.attempts
        return 0

    async def invalidate_previous(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        purpose: VendorOTPPurpose = VendorOTPPurpose.LOGIN,
    ) -> None:
        """Invalidate all previous unused OTPs."""
        conditions = [
            self.model.purpose == purpose,
            self.model.is_used == False,
        ]
        if email:
            conditions.append(self.model.email == email)
        if phone:
            conditions.append(self.model.phone == phone)

        query = select(self.model).where(and_(*conditions))
        result = await self.session.execute(query)
        otps = result.scalars().all()

        for otp in otps:
            otp.is_used = True
        await self.session.flush()
