"""Vendor Registration Service."""

from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    ValidationException,
)
from app.repositories.vendor_portal.registration_repo import (
    VendorRegistrationRepository,
    VendorRegistrationDocumentRepository,
)
from app.repositories.vendor_portal.portal_vendor_user_repo import (
    PortalVendorUserRepository,
)
from app.repositories.ap_ar.vendor_repo import VendorRepository
from app.models.vendor_portal.registration import (
    VendorRegistration,
    VendorRegistrationDocument,
)
from app.models.vendor_portal.portal_vendor_user import PortalVendorUser
from app.models.vendor_portal.enums import (
    RegistrationStatus,
    RegistrationDocumentType,
    VendorPortalUserStatus,
)
from app.schemas.vendor_portal.registration import (
    VendorRegistrationCreate,
    VendorRegistrationUpdate,
    VendorRegistrationDocumentCreate,
)


class VendorRegistrationService:
    """Service for vendor registration operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.reg_repo = VendorRegistrationRepository(session)
        self.doc_repo = VendorRegistrationDocumentRepository(session)
        self.user_repo = PortalVendorUserRepository(session)
        self.vendor_repo = VendorRepository(session)

    async def create_registration(
        self,
        data: VendorRegistrationCreate,
    ) -> VendorRegistration:
        """Create a new registration."""
        # Check for duplicate PAN
        existing_pan = await self.reg_repo.get_by_pan(
            data.pan, data.organization_id
        )
        if existing_pan:
            raise ConflictException(
                f"Registration with PAN {data.pan} already exists"
            )

        # Check for duplicate GSTIN
        if data.gstin:
            existing_gstin = await self.reg_repo.get_by_gstin(
                data.gstin, data.organization_id
            )
            if existing_gstin:
                raise ConflictException(
                    f"Registration with GSTIN {data.gstin} already exists"
                )

        # Check for duplicate email
        existing_email = await self.reg_repo.get_by_email(
            data.contact_email, data.organization_id
        )
        if existing_email:
            raise ConflictException(
                f"Registration with email {data.contact_email} already exists"
            )

        # Generate registration number
        registration_number = await self.reg_repo.generate_registration_number(
            data.organization_id
        )

        # Create registration
        reg_data = data.model_dump()
        reg_data["registration_number"] = registration_number
        reg_data["status"] = RegistrationStatus.DRAFT

        registration = await self.reg_repo.create(reg_data)
        await self.session.flush()

        return registration

    async def update_registration(
        self,
        id: UUID,
        data: VendorRegistrationUpdate,
    ) -> VendorRegistration:
        """Update a registration."""
        registration = await self.reg_repo.get(id)
        if not registration:
            raise NotFoundException("Registration not found")

        if registration.status not in [
            RegistrationStatus.DRAFT,
            RegistrationStatus.ADDITIONAL_INFO_REQUIRED,
        ]:
            raise ValidationException(
                f"Cannot update registration in {registration.status.value} status"
            )

        update_data = data.model_dump(exclude_unset=True)

        # Handle additional info response
        if data.additional_info_response:
            update_data["additional_info_responded_at"] = datetime.utcnow()

        registration = await self.reg_repo.update(registration, update_data)
        await self.session.flush()

        return registration

    async def submit_registration(
        self,
        id: UUID,
        terms_accepted: bool = True,
        terms_version: str = "1.0",
    ) -> VendorRegistration:
        """Submit registration for review."""
        registration = await self.reg_repo.get_with_documents(id)
        if not registration:
            raise NotFoundException("Registration not found")

        if registration.status not in [
            RegistrationStatus.DRAFT,
            RegistrationStatus.ADDITIONAL_INFO_REQUIRED,
        ]:
            raise ValidationException(
                f"Cannot submit registration in {registration.status.value} status"
            )

        if not terms_accepted:
            raise ValidationException("Terms must be accepted to submit")

        # Validate required documents
        required_docs = [
            RegistrationDocumentType.PAN_CARD,
            RegistrationDocumentType.CANCELLED_CHEQUE,
        ]
        if registration.gstin:
            required_docs.append(RegistrationDocumentType.GST_CERTIFICATE)

        uploaded_types = {doc.document_type for doc in registration.documents}
        missing_docs = [doc for doc in required_docs if doc not in uploaded_types]

        if missing_docs:
            raise ValidationException(
                f"Missing required documents: {[d.value for d in missing_docs]}"
            )

        # Update status
        registration.status = RegistrationStatus.SUBMITTED
        registration.submitted_at = datetime.utcnow()
        registration.terms_accepted = terms_accepted
        registration.terms_accepted_at = datetime.utcnow()
        registration.terms_version = terms_version

        await self.session.flush()

        return registration

    async def approve_registration(
        self,
        id: UUID,
        reviewed_by: UUID,
        remarks: Optional[str] = None,
    ) -> VendorRegistration:
        """Approve a registration and create vendor + portal user."""
        registration = await self.reg_repo.get_with_documents(id)
        if not registration:
            raise NotFoundException("Registration not found")

        if registration.status != RegistrationStatus.SUBMITTED:
            raise ValidationException(
                f"Cannot approve registration in {registration.status.value} status"
            )

        # Create vendor master
        vendor = await self._create_vendor_from_registration(registration)

        # Create portal user
        portal_user = await self._create_portal_user_from_registration(
            registration, vendor.id
        )

        # Update registration
        registration.status = RegistrationStatus.APPROVED
        registration.reviewed_by_id = reviewed_by
        registration.reviewed_at = datetime.utcnow()
        registration.review_remarks = remarks
        registration.approved_at = datetime.utcnow()
        registration.vendor_id = vendor.id
        registration.portal_user_id = portal_user.id

        await self.session.flush()

        # TODO: Send welcome email to vendor

        return registration

    async def reject_registration(
        self,
        id: UUID,
        reviewed_by: UUID,
        reason: str,
        category: Optional[str] = None,
    ) -> VendorRegistration:
        """Reject a registration."""
        registration = await self.reg_repo.get(id)
        if not registration:
            raise NotFoundException("Registration not found")

        if registration.status != RegistrationStatus.SUBMITTED:
            raise ValidationException(
                f"Cannot reject registration in {registration.status.value} status"
            )

        registration.status = RegistrationStatus.REJECTED
        registration.reviewed_by_id = reviewed_by
        registration.reviewed_at = datetime.utcnow()
        registration.rejection_reason = reason
        registration.rejection_category = category

        await self.session.flush()

        # TODO: Send rejection email to vendor

        return registration

    async def request_additional_info(
        self,
        id: UUID,
        reviewed_by: UUID,
        request: str,
    ) -> VendorRegistration:
        """Request additional information from vendor."""
        registration = await self.reg_repo.get(id)
        if not registration:
            raise NotFoundException("Registration not found")

        if registration.status != RegistrationStatus.SUBMITTED:
            raise ValidationException(
                f"Cannot request info for registration in {registration.status.value} status"
            )

        registration.status = RegistrationStatus.ADDITIONAL_INFO_REQUIRED
        registration.reviewed_by_id = reviewed_by
        registration.additional_info_requested_at = datetime.utcnow()
        registration.additional_info_request = request

        await self.session.flush()

        # TODO: Send email to vendor requesting additional info

        return registration

    async def get_registration(self, id: UUID) -> VendorRegistration:
        """Get registration by ID."""
        registration = await self.reg_repo.get_with_documents(id)
        if not registration:
            raise NotFoundException("Registration not found")
        return registration

    async def get_all_registrations(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[RegistrationStatus] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[VendorRegistration], int]:
        """Get all registrations."""
        return await self.reg_repo.get_all_by_organization(
            organization_id, skip, limit, status, search
        )

    async def add_document(
        self,
        registration_id: UUID,
        data: VendorRegistrationDocumentCreate,
        file_path: str,
        file_size: int,
        mime_type: str,
        original_filename: str,
    ) -> VendorRegistrationDocument:
        """Add document to registration."""
        registration = await self.reg_repo.get(registration_id)
        if not registration:
            raise NotFoundException("Registration not found")

        if registration.status not in [
            RegistrationStatus.DRAFT,
            RegistrationStatus.ADDITIONAL_INFO_REQUIRED,
        ]:
            raise ValidationException("Cannot add documents in current status")

        # Check if document type already exists
        existing = await self.doc_repo.get_by_type(
            registration_id, data.document_type
        )
        if existing:
            # Soft delete the old one
            await self.doc_repo.soft_delete(existing.id)

        doc_data = {
            "registration_id": registration_id,
            "document_type": data.document_type,
            "document_name": data.document_name,
            "document_number": data.document_number,
            "issue_date": data.issue_date,
            "expiry_date": data.expiry_date,
            "file_path": file_path,
            "file_size": file_size,
            "mime_type": mime_type,
            "original_filename": original_filename,
        }

        document = await self.doc_repo.create(doc_data)
        await self.session.flush()

        return document

    # Private helper methods
    async def _create_vendor_from_registration(
        self, registration: VendorRegistration
    ):
        """Create vendor master from registration."""
        from app.models.ap_ar.vendor import Vendor, VendorType, MSMEType

        # Generate vendor code
        vendor_code = await self.vendor_repo.generate_vendor_code(
            registration.organization_id
        )

        # Determine MSME type
        msme_type = MSMEType.NOT_APPLICABLE
        if registration.msme_category:
            msme_type = MSMEType(registration.msme_category.upper())

        vendor_data = {
            "code": vendor_code,
            "name": registration.company_name,
            "display_name": registration.trade_name or registration.company_name,
            "vendor_type": VendorType.SUPPLIER,
            "organization_id": registration.organization_id,
            "pan": registration.pan,
            "gstin": registration.gstin,
            "msme_registered": bool(registration.msme_number),
            "msme_number": registration.msme_number,
            "msme_type": msme_type,
            "contact_person": registration.contact_name,
            "email": registration.contact_email,
            "phone": registration.contact_phone,
            "address_line1": registration.registered_address,
            "city": registration.city,
            "state_code": registration.state_code,
            "pincode": registration.pincode,
            "country": registration.country,
            "bank_name": registration.bank_name,
            "bank_branch": registration.bank_branch,
            "bank_account_number": registration.account_number,
            "bank_ifsc_code": registration.ifsc_code,
        }

        vendor = await self.vendor_repo.create(vendor_data)
        return vendor

    async def _create_portal_user_from_registration(
        self, registration: VendorRegistration, vendor_id: UUID
    ) -> PortalVendorUser:
        """Create portal user from registration."""
        user_data = {
            "vendor_id": vendor_id,
            "organization_id": registration.organization_id,
            "email": registration.contact_email,
            "phone": registration.contact_phone,
            "first_name": registration.contact_name.split()[0],
            "last_name": " ".join(registration.contact_name.split()[1:]) or "",
            "designation": registration.contact_designation,
            "is_primary_contact": True,
            "email_verified": False,
            "phone_verified": False,
            "status": VendorPortalUserStatus.ACTIVE,
            "can_view_pos": True,
            "can_acknowledge_pos": True,
            "can_submit_invoices": True,
            "can_create_asn": True,
            "can_view_payments": True,
            "can_manage_users": True,
            "can_manage_compliance": True,
        }

        user = await self.user_repo.create(user_data)
        return user
