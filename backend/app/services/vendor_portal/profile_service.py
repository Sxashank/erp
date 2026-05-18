"""Vendor Profile Service."""

from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    ValidationException,
)
from app.repositories.vendor_portal.portal_vendor_user_repo import (
    PortalVendorUserRepository,
)
from app.repositories.ap_ar.vendor_repo import VendorRepository
from app.models.vendor_portal.portal_vendor_user import PortalVendorUser
from app.models.vendor_portal.enums import VendorPortalUserStatus
from app.models.ap_ar.vendor import Vendor
from app.schemas.vendor_portal.profile import (
    VendorProfileUpdate,
    VendorBankAccountCreate,
    VendorBankAccountUpdate,
    VendorContactCreate,
    VendorContactUpdate,
    PortalUserCreate,
    PortalUserUpdate,
    PortalUserPermissions,
)


class VendorProfileService:
    """Service for vendor profile management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = PortalVendorUserRepository(session)
        self.vendor_repo = VendorRepository(session)

    async def get_vendor_profile(
        self,
        vendor_id: UUID,
    ) -> Vendor:
        """Get vendor profile."""
        vendor = await self.vendor_repo.get_with_details(vendor_id)
        if not vendor:
            raise NotFoundException("Vendor not found")
        return vendor

    async def update_vendor_profile(
        self,
        vendor_id: UUID,
        updated_by_id: UUID,
        data: VendorProfileUpdate,
    ) -> Vendor:
        """Update vendor profile."""
        vendor = await self.vendor_repo.get(vendor_id)
        if not vendor:
            raise NotFoundException("Vendor not found")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by_id"] = updated_by_id
        update_data["updated_at"] = datetime.utcnow()

        vendor = await self.vendor_repo.update(vendor, update_data)
        await self.session.flush()

        return vendor

    async def get_bank_accounts(
        self,
        vendor_id: UUID,
    ) -> List[dict]:
        """Get vendor bank accounts."""
        vendor = await self.vendor_repo.get(vendor_id)
        if not vendor:
            raise NotFoundException("Vendor not found")

        # Return bank account info from vendor
        accounts = []
        if vendor.bank_account_number:
            accounts.append({
                "id": vendor_id,
                "bank_name": vendor.bank_name,
                "branch": vendor.bank_branch,
                "account_number": vendor.bank_account_number,
                "ifsc_code": vendor.bank_ifsc_code,
                "is_primary": True,
            })
        return accounts

    async def add_bank_account(
        self,
        vendor_id: UUID,
        data: VendorBankAccountCreate,
    ) -> dict:
        """Add bank account to vendor."""
        vendor = await self.vendor_repo.get(vendor_id)
        if not vendor:
            raise NotFoundException("Vendor not found")

        # Update primary bank account
        vendor.bank_name = data.bank_name
        vendor.bank_branch = data.branch
        vendor.bank_account_number = data.account_number
        vendor.bank_ifsc_code = data.ifsc_code

        await self.session.flush()

        return {
            "id": vendor_id,
            "bank_name": data.bank_name,
            "branch": data.branch,
            "account_number": data.account_number,
            "ifsc_code": data.ifsc_code,
            "is_primary": True,
        }

    async def update_bank_account(
        self,
        vendor_id: UUID,
        account_id: UUID,
        data: VendorBankAccountUpdate,
    ) -> dict:
        """Update bank account."""
        vendor = await self.vendor_repo.get(vendor_id)
        if not vendor:
            raise NotFoundException("Vendor not found")

        update_data = data.model_dump(exclude_unset=True)
        if "bank_name" in update_data:
            vendor.bank_name = update_data["bank_name"]
        if "branch" in update_data:
            vendor.bank_branch = update_data["branch"]
        if "account_number" in update_data:
            vendor.bank_account_number = update_data["account_number"]
        if "ifsc_code" in update_data:
            vendor.bank_ifsc_code = update_data["ifsc_code"]

        await self.session.flush()

        return {
            "id": vendor_id,
            "bank_name": vendor.bank_name,
            "branch": vendor.bank_branch,
            "account_number": vendor.bank_account_number,
            "ifsc_code": vendor.bank_ifsc_code,
            "is_primary": True,
        }

    async def get_contacts(
        self,
        vendor_id: UUID,
    ) -> List[PortalVendorUser]:
        """Get vendor portal contacts."""
        users = await self.user_repo.get_by_vendor(vendor_id)
        return users

    async def add_contact(
        self,
        vendor_id: UUID,
        organization_id: UUID,
        data: VendorContactCreate,
        invited_by_id: UUID,
    ) -> PortalVendorUser:
        """Add contact (portal user) to vendor."""
        vendor = await self.vendor_repo.get(vendor_id)
        if not vendor:
            raise NotFoundException("Vendor not found")

        # Check for duplicate email
        existing = await self.user_repo.get_by_email(data.email, organization_id)
        if existing:
            raise ConflictException(f"User with email {data.email} already exists")

        user_data = {
            "vendor_id": vendor_id,
            "organization_id": organization_id,
            "email": data.email,
            "phone": data.phone,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "designation": data.designation,
            "department": data.department,
            "is_primary_contact": False,
            "status": VendorPortalUserStatus.PENDING_ACTIVATION,
            "invited_by_id": invited_by_id,
            "invited_at": datetime.utcnow(),
        }

        user = await self.user_repo.create(user_data)
        await self.session.flush()

        # TODO: Send invitation email to user

        return user

    async def update_contact(
        self,
        vendor_id: UUID,
        contact_id: UUID,
        data: VendorContactUpdate,
    ) -> PortalVendorUser:
        """Update contact."""
        user = await self.user_repo.get(contact_id)
        if not user:
            raise NotFoundException("Contact not found")

        if user.vendor_id != vendor_id:
            raise ValidationException("Contact does not belong to this vendor")

        update_data = data.model_dump(exclude_unset=True)
        user = await self.user_repo.update(user, update_data)
        await self.session.flush()

        return user

    async def remove_contact(
        self,
        vendor_id: UUID,
        contact_id: UUID,
    ) -> None:
        """Remove contact (deactivate)."""
        user = await self.user_repo.get(contact_id)
        if not user:
            raise NotFoundException("Contact not found")

        if user.vendor_id != vendor_id:
            raise ValidationException("Contact does not belong to this vendor")

        if user.is_primary_contact:
            raise ValidationException("Cannot remove primary contact")

        user.status = VendorPortalUserStatus.DEACTIVATED
        user.deactivated_at = datetime.utcnow()

        await self.session.flush()

    async def get_portal_users(
        self,
        vendor_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[VendorPortalUserStatus] = None,
    ) -> Tuple[List[PortalVendorUser], int]:
        """Get portal users for a vendor."""
        return await self.user_repo.get_all_by_vendor(
            vendor_id, skip, limit, status
        )

    async def create_portal_user(
        self,
        vendor_id: UUID,
        organization_id: UUID,
        data: PortalUserCreate,
        created_by_id: UUID,
    ) -> PortalVendorUser:
        """Create a new portal user."""
        vendor = await self.vendor_repo.get(vendor_id)
        if not vendor:
            raise NotFoundException("Vendor not found")

        # Check for duplicate email
        existing = await self.user_repo.get_by_email(data.email, organization_id)
        if existing:
            raise ConflictException(f"User with email {data.email} already exists")

        user_data = data.model_dump()
        user_data.update({
            "vendor_id": vendor_id,
            "organization_id": organization_id,
            "status": VendorPortalUserStatus.PENDING_ACTIVATION,
            "invited_by_id": created_by_id,
            "invited_at": datetime.utcnow(),
        })

        user = await self.user_repo.create(user_data)
        await self.session.flush()

        # TODO: Send invitation email

        return user

    async def update_portal_user(
        self,
        vendor_id: UUID,
        user_id: UUID,
        data: PortalUserUpdate,
    ) -> PortalVendorUser:
        """Update portal user."""
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException("User not found")

        if user.vendor_id != vendor_id:
            raise ValidationException("User does not belong to this vendor")

        update_data = data.model_dump(exclude_unset=True)
        user = await self.user_repo.update(user, update_data)
        await self.session.flush()

        return user

    async def update_user_permissions(
        self,
        vendor_id: UUID,
        user_id: UUID,
        permissions: PortalUserPermissions,
    ) -> PortalVendorUser:
        """Update user permissions."""
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException("User not found")

        if user.vendor_id != vendor_id:
            raise ValidationException("User does not belong to this vendor")

        perm_data = permissions.model_dump()
        user = await self.user_repo.update(user, perm_data)
        await self.session.flush()

        return user

    async def activate_user(
        self,
        user_id: UUID,
    ) -> PortalVendorUser:
        """Activate a pending user."""
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException("User not found")

        if user.status != VendorPortalUserStatus.PENDING_ACTIVATION:
            raise ValidationException(
                f"Cannot activate user in {user.status.value} status"
            )

        user.status = VendorPortalUserStatus.ACTIVE
        user.activated_at = datetime.utcnow()

        await self.session.flush()

        return user

    async def deactivate_user(
        self,
        vendor_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None,
    ) -> PortalVendorUser:
        """Deactivate a user."""
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException("User not found")

        if user.vendor_id != vendor_id:
            raise ValidationException("User does not belong to this vendor")

        if user.is_primary_contact:
            raise ValidationException("Cannot deactivate primary contact")

        user.status = VendorPortalUserStatus.DEACTIVATED
        user.deactivated_at = datetime.utcnow()
        user.deactivation_reason = reason

        await self.session.flush()

        return user

    async def set_primary_contact(
        self,
        vendor_id: UUID,
        user_id: UUID,
    ) -> PortalVendorUser:
        """Set user as primary contact."""
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException("User not found")

        if user.vendor_id != vendor_id:
            raise ValidationException("User does not belong to this vendor")

        if user.status != VendorPortalUserStatus.ACTIVE:
            raise ValidationException("Only active users can be primary contact")

        # Remove primary flag from current primary
        current_primary = await self.user_repo.get_primary_contact(vendor_id)
        if current_primary and current_primary.id != user_id:
            current_primary.is_primary_contact = False

        user.is_primary_contact = True

        await self.session.flush()

        return user
